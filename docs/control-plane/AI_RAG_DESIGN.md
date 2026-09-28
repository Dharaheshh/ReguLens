# AI_RAG_DESIGN.md — Retrieval and LLM Call Design

This file defines every LLM call in the system (there are exactly four) and
the deterministic retrieval/validation logic around them. The RAG/validation
boundary from `ARCHITECTURE.md` applies throughout: retrieval finds candidates,
it never judges truth or sufficiency.

## Document ingestion pipeline (deterministic, no LLM)

```
PDF uploaded
  → parse (extract text, preserve page numbers and detected section headings)
  → section-aware chunking (split on headings/paragraphs, not fixed character
    counts, target ~500 tokens per chunk, never split mid-sentence where
    avoidable)
  → for each chunk: generate embedding via the configured embedding model
    (dimension must match chunks.embedding column — see ENVIRONMENT.md)
  → insert chunk row (with embedding + tsv auto-generated)
  → insert one evidence row per chunk, evidence_code assigned sequentially
    (EVD-00001, EVD-00002, ...)
```

**Failure modes:**
- Parser can't extract text (scanned/image PDF) → reject upload with
  `400 UNSUPPORTED_DOCUMENT` (OCR is out of scope — see `PROJECT_CONTEXT.md`)
- Embedding API call fails → retry once, then fail the whole upload with
  `500 INGESTION_FAILED` (partial ingestion is not allowed — either a
  document is fully ingested or not ingested at all)

## Hybrid retrieval (deterministic, no LLM)

For a given search string (a requirement's description + keywords):

```
lexical_results  = SELECT * FROM chunks
                    WHERE tsv @@ plainto_tsquery('english', :search_string)
                    ORDER BY ts_rank(tsv, plainto_tsquery('english', :search_string)) DESC
                    LIMIT 20

vector_results   = SELECT * FROM chunks
                    ORDER BY embedding <=> :query_embedding
                    LIMIT 20

fused = reciprocal_rank_fusion(lexical_results, vector_results)
        # combine by rank position, not raw score — the two scoring scales
        # (ts_rank vs cosine distance) are not directly comparable
```

Reciprocal rank fusion (RRF): for each chunk, `score = sum(1 / (60 + rank))`
across whichever list(s) it appears in; higher combined score wins. This is a
well-established, parameter-light way to combine two differently-scaled
ranked lists without inventing a weighting scheme.

**Why hybrid, not vector-only:** semantic search finds paraphrases
("pathogen screening" for a "microbiological safety" query) but can blur past
exact regulatory terms and thresholds; lexical search nails exact terms but
misses paraphrasing. Fusing both catches what either alone would miss.

## Reranking (should-have, deterministic non-generative model)

If implemented: pass the fused top-20 through a cross-encoder reranker,
re-score, take the new top-k (k=5 default). This is a scoring model, not a
generative LLM call — no schema validation needed, just a float score per
candidate.

**Failure mode:** reranker unavailable/errors → fall back to the RRF-fused
order directly, log a warning, continue (this stage is should-have — its
absence never blocks the pipeline).

---

## LLM Call 1 — Requirement Extraction

**Purpose:** decompose a regulator query into discrete, checkable
requirements, so sufficiency can be computed per sub-question instead of as
one vague judgment.

**Input:**
```json
{ "query_text": "Provide evidence supporting the microbiological safety of the cultivated-cell product and describe the controls used during production." }
```

**Output schema (Pydantic):**
```python
class Requirement(BaseModel):
    req_code: str          # "REQ-01"
    description: str
    keywords: list[str]

class RequirementExtractionOutput(BaseModel):
    requirements: list[Requirement]  # min_length=1
```

**Temperature:** 0.2
**Validation:** Pydantic parse; reject if `requirements` is empty.
**Retry:** 1 retry with the validation error appended to the prompt.
**Failure state:** after 1 failed retry, fallback — treat the entire query
text as a single `REQ-01` requirement (never block the pipeline entirely on
this stage).

---

## LLM Call 2 — Response Generation (draft + claim + citation proposal)

**Purpose:** draft the regulator response text, decomposed into individual
claims, each with proposed supporting evidence IDs. This single call produces
both the draft and its claim/citation structure — no separate "claim
extraction" call is needed, because forcing structured output at generation
time is more reliable than re-parsing free text afterward.

**Input:**
```json
{
  "query_text": "...",
  "requirements": [{"req_code": "REQ-01", "description": "..."}],
  "evidence_pack": [
    {"evidence_code": "EVD-01872", "text": "No detectable microbial contamination was observed above the assay reporting threshold...", "source_type": "internal_study"}
  ]
}
```
The evidence pack text is wrapped as clearly delimited untrusted content (see
`SECURITY.md`) — never concatenated as if it were part of the system prompt's
instructions.

**Output schema:**
```python
class ClaimProposal(BaseModel):
    claim_code: str            # "CLM-0042"
    claim_text: str
    product_topic: str
    req_code: str               # which requirement this claim addresses
    cited_evidence_codes: list[str]   # e.g. ["EVD-01872"] — proposed, not yet validated

class ResponseGenerationOutput(BaseModel):
    draft_text: str
    claims: list[ClaimProposal]
```

**Temperature:** 0.2
**System prompt responsibility:** instruct the model to only cite evidence
codes present in the supplied evidence pack, to never invent an evidence code,
and to keep claim language no broader than what the cited evidence states.
**Validation:** Pydantic parse.
**Retry:** 1 retry with validation error appended.
**Failure state:** `LLM_FAILED` — the whole query attempt fails, surfaced to
the user with a retry option; nothing partial is persisted.

**What happens after this call (deterministic):** every `cited_evidence_codes`
entry is looked up against the `evidence` table. Found → a `citations` row is
created with `validated = true`. Not found → no citation row is created and
that claim's initial state is set to consider it in the validation call below.

---

## LLM Call 3 — Claim ↔ Evidence Validation

**Purpose:** determine whether each claim, given only the evidence it
actually has validated citations for, is truly supported, partially
supported, unsupported, or an overclaim.

**Input (per claim):**
```json
{
  "claim_text": "No microbial contamination was detected.",
  "cited_evidence": [
    {"evidence_code": "EVD-001", "text": "Microbial signal was detected in 1 of 100 samples, below the reporting threshold.", "source_type": "internal_study"}
  ]
}
```

Note: only the evidence this specific claim has *validated* citations for is
included — not the full evidence pack, not surrounding context. This
narrowness is deliberate: it's what makes the validation a real check rather
than a chance for the model to rationalize using material the claim didn't
actually cite.

**Deterministic pre-check (before this LLM call is even made):** if a claim
has zero validated citations (all its proposed evidence codes failed
resolution), it is set to `UNSUPPORTED` directly — no LLM call needed.

**Output schema:**
```python
class ClaimValidationOutput(BaseModel):
    validation_state: Literal["SUPPORTED", "PARTIALLY_SUPPORTED", "OVERCLAIM", "CONFLICTING"]
    reasoning: str
    supported_portion: str   # what the evidence actually supports, in the model's words
```

**Temperature:** 0.1 (this call most benefits from consistency)
**Validation:** Pydantic parse; `validation_state` must be one of the four
literal values.
**Retry:** 1 retry.
**Failure state:** `VALIDATION_FAILED` for that claim — the claim is still
shown to the reviewer, flagged as unvalidated, never silently marked
`SUPPORTED` by default.

**Worked example (the overclaim case):** evidence says "signal detected in 1
of 100 samples, below reporting threshold"; claim says "no contamination was
detected." The model is structurally required to name the `supported_portion`
— it cannot just emit a label, it must state what narrower claim the evidence
would actually support ("contamination was not detected above the assay
reporting threshold"), which makes the OVERCLAIM classification auditable
rather than an opaque verdict.

---

## LLM Call 4 — Contradiction Comparison

**Purpose:** for a new claim, compare it against each of its deterministically
pre-filtered historical candidates (see `ARCHITECTURE.md` candidate selection
query) and classify the relationship.

**Deterministic pre-filter (repeated here for completeness — defined once in
`ARCHITECTURE.md`):** candidates = claims sharing `product_topic`, belonging
to `approved` responses, capped at 10, most recent first. **Semantic
similarity is explicitly not used as a filter or as the classification
itself** — it is not computed at this stage at all. The filter is topic +
approval status only; the actual judgment of whether two claims truly
conflict is left entirely to the scoped LLM call below, which can weigh
threshold/unit/date/scope differences that pure similarity would miss or
over-trigger on.

**Input (per candidate pair):**
```json
{
  "new_claim": {"text": "...", "date": "...", "document_version": "v3"},
  "historical_claim": {"text": "...", "date": "...", "document_version": "v1", "response_id": "..."}
}
```

**Output schema:**
```python
class ContradictionOutput(BaseModel):
    classification: Literal["COMPATIBLE", "POTENTIAL_CONTRADICTION", "LIKELY_CONTRADICTION", "INSUFFICIENT_CONTEXT"]
    reasoning: str
    distinguishing_factors_considered: list[str]  # e.g. ["threshold", "assay_sensitivity"]
```

**Temperature:** 0.1
**System prompt responsibility:** explicitly instruct the model to consider
product version, date, threshold, units, and study conditions before
classifying anything as a contradiction — not to rely on surface wording
alone.
**Validation:** Pydantic parse.
**Retry:** 1 retry.
**Failure state:** `INSUFFICIENT_CONTEXT` — never silently skip a candidate
pair; an unresolvable comparison is itself a signal for human attention.

**Persistence:** only non-`COMPATIBLE` results are written to
`contradictions` (see `DATABASE_SCHEMA.md`).

---

## Evidence Sufficiency Engine (fully deterministic — no LLM call)

Per-requirement coverage state, computed from `requirement_evidence` rows:

```
top_score = max(retrieval_score for this requirement's requirement_evidence rows)
match_count = count(requirement_evidence rows for this requirement)

if top_score >= THRESHOLD_HIGH and match_count >= 2:
    status = COVERED
elif top_score >= THRESHOLD_LOW:
    status = PARTIALLY_COVERED
else:
    status = NOT_COVERED
```

`THRESHOLD_HIGH` / `THRESHOLD_LOW` are calibrated against the actual corpus
during testing (starting point: 0.75 / 0.55 on the fused RRF score, adjusted
based on real retrieval behavior — see `TESTING_STRATEGY.md`).

Overall response-level status (deterministic aggregation):
```
if all requirements COVERED:                             SUFFICIENT
elif any requirement NOT_COVERED:                          INSUFFICIENT
elif any requirement PARTIALLY_COVERED (none NOT_COVERED):  PARTIALLY_SUFFICIENT
```

The gap summary shown to the user is generated by deterministic string
formatting over the `NOT_COVERED`/`PARTIALLY_COVERED` requirement rows — not
a fifth LLM call. This keeps the sufficiency verdict fully traceable to
stored numbers, per `RULES.md` rule #10.

## Summary: LLM calls vs. deterministic logic

| Stage | LLM? |
|---|---|
| Parsing, chunking, embedding | No |
| Hybrid retrieval, fusion | No |
| Reranking | No (a scoring model, not generative) |
| Requirement extraction | **Yes** — Call 1 |
| Response draft + claim/citation proposal | **Yes** — Call 2 |
| Citation ID resolution | No |
| Claim ↔ evidence validation | **Yes** — Call 3 |
| Contradiction candidate pre-filter | No |
| Contradiction classification | **Yes** — Call 4 |
| Sufficiency scoring and aggregation | No |
| Gap summary text | No |

Four LLM calls total. Everything else is deterministic code, by design.

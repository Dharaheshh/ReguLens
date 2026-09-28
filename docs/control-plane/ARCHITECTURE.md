# ARCHITECTURE.md — Canonical Technical Architecture

This is the approved architecture. It is locked. Do not redesign any part of it
during implementation — see `AGENTS.md` for what to do if it seems wrong.

## System diagram

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend — React + TypeScript + Vite + Tailwind             │
│  (Document Library, Query Workspace, Evidence/Citation        │
│   Viewer, Contradiction Panel, Sufficiency/Gap View,           │
│   Review + Audit Trail panel)                                  │
└───────────────────────────┬─────────────────────────────────┘
                             │ REST / JSON (see API_CONTRACT.md)
┌───────────────────────────▼─────────────────────────────────┐
│  Backend — Python + FastAPI                                   │
│                                                                 │
│  ├─ ingestion/     parse PDF → chunk → embed → store            │
│  ├─ retrieval/     hybrid BM25 + HNSW search, fusion, rerank      │
│  ├─ generation/    requirement extraction, response draft,         │
│  │                 claim/citation proposal (LLM calls)              │
│  └─ validation/    citation validator, claim/evidence validator,      │
│                    contradiction engine, sufficiency engine             │
│                    (deterministic + scoped LLM calls)                     │
└───────────────────────────┬─────────────────────────────────┘
                             │
┌───────────────────────────▼─────────────────────────────────┐
│  PostgreSQL + pgvector — single database, sole source of truth │
│  documents, document_versions, chunks, evidence,                │
│  regulatory_queries, requirements, requirement_evidence,          │
│  responses, claims, citations, contradictions, audit_events         │
└───────────────────────────┬─────────────────────────────────┘
                             │
┌───────────────────────────▼─────────────────────────────────┐
│  Anthropic Claude API — structured JSON output only.            │
│  Used ONLY for: requirement extraction, response drafting/         │
│  claim+citation proposal, claim/evidence validation reasoning,        │
│  contradiction comparison. NEVER used for: citation existence           │
│  checks, sufficiency aggregation, auth, or any step that must             │
│  be provably correct rather than merely well-reasoned.                      │
└─────────────────────────────────────────────────────────────────┘
```

## Component responsibilities

| Component | Responsibility | Does NOT do |
|---|---|---|
| `ingestion/` | Parse PDFs, preserve page/section metadata, chunk, generate embeddings, store | Judge relevance, generate text |
| `retrieval/` | Hybrid lexical + vector search, fusion, optional rerank | Judge truth, sufficiency, or claim validity |
| `generation/` | Call the LLM to extract requirements, draft responses, propose claims+citations | Persist anything without validation; decide sufficiency or contradiction |
| `validation/` | Validate citations against DB, validate claim↔evidence support, run contradiction candidate comparison, compute sufficiency | Retrieve evidence; generate new text |
| PostgreSQL | Sole source of truth for every persisted object | Trust anything not yet validated |
| Claude API | Language reasoning: drafting, extraction, comparison | Anything requiring certainty or existence-checking |

## The RAG / validation boundary (explicit, hard line)

**Retrieval's responsibility ends at:** "here are the k most relevant evidence
chunks for this requirement, ranked by score."

**Validation's responsibility begins at:** "does this specific generated claim
actually follow from the specific evidence it cites — and does this claim
conflict with anything previously approved?"

These are separate code paths. Retrieval code never makes a truth judgment.
Validation code never performs a new search — it only reasons over evidence
already retrieved and passed to it.

## Canonical query lifecycle

| # | Stage | Input | Process | Output | Source of truth | LLM or deterministic | Failure behavior |
|---|---|---|---|---|---|---|---|
| 1 | Query normalization | raw query text | trim, validate non-empty | `regulatory_queries` row | DB | Deterministic | Empty query → 400, no write |
| 2 | Requirement extraction | query text | LLM decomposes into checkable requirements | requirements JSON → rows | DB (`requirements`) | LLM, schema-validated | Malformed JSON → 1 retry → fallback: whole query as one requirement |
| 3 | Hybrid retrieval | per-requirement query | BM25 (`tsvector`) + HNSW vector search | ranked candidate chunks | `chunks` table | Deterministic | No matches → requirement marked `NOT_COVERED`, pipeline continues |
| 4 | Reranking (should-have) | candidate chunks | rerank model reorders | reordered top-k | not persisted | Deterministic (non-generative model) | Failure → fall back to fusion order, log warning |
| 5 | Evidence pack assembly | top-k chunks | resolve to `evidence` records with citable IDs | evidence pack | `evidence` table | Deterministic | — |
| 6 | Response generation | evidence pack + query | LLM drafts response, proposes claims + evidence IDs cited | draft JSON | not yet persisted (pending) | LLM, schema-validated | Malformed JSON → 1 retry → `LLM_FAILED` |
| 7 | Citation validation | proposed evidence IDs | look up each ID in `evidence` table | validated/invalid citations | `citations` table | **Deterministic** | Invalid ID → no citation row created, claim downgraded to `UNSUPPORTED` |
| 8 | Claim ↔ evidence validation | claim + its validated evidence | LLM compares meaning, classifies support | validation_state per claim | `claims.validation_state` | LLM, schema-validated | Malformed JSON → retry → `VALIDATION_FAILED`, still shown to reviewer |
| 9 | Historical consistency | new claims + scoped historical claims | deterministic pre-filter, then LLM comparison | contradiction records | `contradictions` table | Hybrid (deterministic filter + LLM) | LLM failure → `INSUFFICIENT_CONTEXT`, never silently skipped |
| 10 | Evidence sufficiency | requirement coverage states | deterministic aggregation | `sufficiency_status` | `responses.sufficiency_status` | Deterministic | — |
| 11 | Review state assembly | all of the above | assemble for reviewer | review-ready response | `responses.status = 'draft'` | Deterministic | — |
| 12 | Human approval | reviewer action | approve / edit / reject | final response, version bump | `responses`, `audit_events` | Human | Rejection → status set, no auto-resubmission |

## Source of truth (canonical table)

| Object | Source of truth |
|---|---|
| documents, document_versions, chunks, evidence, requirements, requirement_evidence, regulatory_queries, responses, claims, citations, contradictions, audit_events | **PostgreSQL** |
| Any LLM call output | **Never** — always a proposal pending validation |
| Frontend component state | **Never** — always re-fetched from backend after mutation |

## Versioning rules

- Old chunks/embeddings are retained forever; never overwritten or deleted.
- A new upload of an existing document creates a new `document_versions` row;
  the previous version's status becomes `superseded`, not deleted.
- Every `evidence` row is permanently tied to one `document_version_id`. Every
  `citation` row is permanently tied to one `evidence` row. This means an
  approved response remains fully auditable even after the source document has
  since been updated.
- Retrieval, by default, only searches non-superseded (current) versions via
  `documents.current_version_id`. Superseded versions remain queryable
  explicitly for audit/comparison purposes.

## Evidence object model

```
Document → DocumentVersion → Chunk → Evidence
```

`Evidence` is a real, persisted table — not a computed view — because it
carries citation-relevant metadata (page range, section, source type) that a
raw `Chunk` doesn't need to carry, and because citations must reference a
stable, permanent object. One `Evidence` row is created per `Chunk` at
ingestion time; retrieval never creates new `Evidence` rows, it only returns
references to existing ones (see `requirement_evidence` for the per-query
relevance score, which is where retrieval-time, per-query data lives —
evidence itself stays stable and reusable).

## Contradiction candidate selection

Before any LLM call, a deterministic filter selects candidates:

```
candidates = SELECT claims
             FROM claims JOIN responses ON claims.response_id = responses.id
             WHERE claims.product_topic = new_claim.product_topic
               AND responses.status = 'approved'
               AND claims.id != new_claim.id
             ORDER BY responses.reviewed_at DESC
             LIMIT 10
```

Only this pre-filtered set is ever passed to the LLM comparison call. The LLM
classifies each pair as `COMPATIBLE`, `POTENTIAL_CONTRADICTION`,
`LIKELY_CONTRADICTION`, or `INSUFFICIENT_CONTEXT` — it never auto-resolves a
contradiction; anything other than `COMPATIBLE` is written to `contradictions`
and surfaced to the human reviewer.

## Evidence sufficiency computation

Deterministic aggregation over stored requirement coverage (see
`AI_RAG_DESIGN.md` for the full per-requirement algorithm):

```
if all requirements COVERED:                           SUFFICIENT
elif any requirement NOT_COVERED:                       INSUFFICIENT
elif any requirement PARTIALLY_COVERED (none NOT_COVERED): PARTIALLY_SUFFICIENT
```

Any coverage percentage shown in the UI is explicitly labeled as a
retrieval-coverage measure — never framed as a scientific-completeness or
safety score.

## Human review boundary

Every response, regardless of its sufficiency status, validation results, or
contradiction findings, stops at `responses.status = 'draft'` and requires an
explicit human `approve` action — logged in `audit_events` with actor and
timestamp — before it can be exported. There is no code path that
auto-approves a response.

## Canonical failure/system states

| State | Generated by | Stops workflow? | Requires human review? |
|---|---|---|---|
| `SUFFICIENT` / `PARTIALLY_SUFFICIENT` / `INSUFFICIENT` | Sufficiency engine | No | Yes (all responses reviewed) |
| `SUPPORTED` / `PARTIALLY_SUPPORTED` / `UNSUPPORTED` / `OVERCLAIM` | Claim validation | No | Yes |
| `COMPATIBLE` / `POTENTIAL_CONTRADICTION` / `LIKELY_CONTRADICTION` / `INSUFFICIENT_CONTEXT` | Contradiction engine | No | Yes if non-`COMPATIBLE` |
| `VALIDATION_FAILED` | Any LLM call failing schema validation after retry | No — degrades gracefully | Yes, reviewer sees what failed |
| `RETRIEVAL_FAILED` | DB/search error | Yes, for that requirement only | N/A — surfaced as a bug |
| `LLM_FAILED` | API timeout/error after retry | Yes, for that response | N/A |

## What must never be automated

The system may: retrieve, extract requirements, draft language, classify
claim-support, classify contradiction likelihood, classify sufficiency,
generate a gap map, propose citations (backend-validated before use).

The system must never: declare that a product is safe, invent an evidence ID
or document that doesn't exist, silently resolve a `LIKELY_CONTRADICTION`,
auto-approve or auto-submit any response.

## Why this stack and not more

- **Single PostgreSQL + pgvector database**, not a dedicated vector database:
  at hackathon scale (a few thousand chunks), HNSW inside Postgres gives the
  same core algorithm without a second system to deploy and keep in sync with
  relational data.
- **Synchronous request/response**, not an async job queue: ingesting ~40
  documents takes seconds per file, not minutes — a queue would add real
  infrastructure for a problem that doesn't exist at this scale.
- **Hybrid deterministic + scoped-LLM validation**, not pure rules or pure LLM:
  pure rules would miss nuanced contradictions in natural language; pure LLM
  judgment would be unauditable and prone to false positives. The deterministic
  pre-filter narrows candidates to a trustworthy set before the LLM reasons
  about meaning within it.
- **No Kafka/Redis/Neo4j/Kubernetes/Celery/microservices**: none of these solve
  a problem this system actually has at this scale. Every exclusion is
  deliberate, not an oversight.

# TESTING_STRATEGY.md — Complete Testing Matrix

Every feature in `TASKS.md` has at least one test here targeting its core
behavior. "Works when I clicked through it once" is not a test — see
`DEFINITION_OF_DONE.md`.

## Unit tests

| Component | Test | Expected |
|---|---|---|
| Chunking | Feed a known 3-page fixture PDF's extracted text | Produces chunks with correct `page_start`/`page_end`, no mid-sentence splits at section boundaries |
| Citation validator | Evidence code that exists in DB | `citations` row created, `validated=true` |
| Citation validator | Evidence code that does NOT exist | No `citations` row created; claim's state reflects unresolved citation |
| Claim validation state machine | Claim with zero validated citations | `UNSUPPORTED`, no LLM call made (deterministic pre-check) |
| Contradiction candidate filter | Claims across different `product_topic` | Not included as candidates |
| Contradiction candidate filter | Claim from a `draft` (not `approved`) response | Not included as candidates |
| Sufficiency aggregation | All requirements `COVERED` | `SUFFICIENT` |
| Sufficiency aggregation | One requirement `NOT_COVERED`, rest `COVERED` | `INSUFFICIENT` |
| Sufficiency aggregation | Mix of `COVERED`/`PARTIALLY_COVERED`, none `NOT_COVERED` | `PARTIALLY_SUFFICIENT` |
| RRF fusion | Two ranked lists with partial overlap | Combined ranking matches manual RRF calculation on a known fixture |
| Pydantic schema validation for each LLM call | Malformed JSON response (fixture) | Raises validation error, triggers retry path |

## Integration tests

| Flow | Test | Expected |
|---|---|---|
| Ingestion | Upload fixture PDF via `POST /documents` | `documents`, `document_versions`, `chunks`, `evidence` rows all created with correct linkage |
| Ingestion — versioning | Upload a second version of the same document | Old version marked `superseded`, `current_version_id` updated, old chunks/evidence untouched |
| Retrieval | Query against seeded corpus for a known topic | Returns the fixture chunk known to be relevant, within top-k |
| Full query pipeline (mocked LLM) | `POST /queries` with fixed mock LLM responses | Response, claims, citations, requirements all persisted with expected relationships |
| Citation resolution end-to-end | Draft proposes one valid + one invalid evidence code | Exactly one `citations` row created; the claim with the invalid code is flagged appropriately |
| Contradiction detection | Seeded planted-contradiction pair (see `EVALUATION_PLAN.md`) | Contradiction detected with classification other than `COMPATIBLE`, written to `contradictions` |
| Sufficiency — insufficient case | Seeded query with deliberately missing evidence category | Response returns `sufficiency_status = INSUFFICIENT` with a correct gap summary |

## API tests

| Endpoint | Test |
|---|---|
| Every endpoint in `API_CONTRACT.md` | Request without auth header → `401` |
| `POST /documents` | Non-PDF file → `400 INVALID_FILE_TYPE` |
| `POST /queries` | Empty `query_text` → `422` |
| `POST /responses/{id}/approve` | Missing `reviewed_by` → `422` |
| `POST /responses/{id}/approve` | Valid request → `200`, `audit_events` row created |
| `GET /evidence/{id}` | Nonexistent ID → `404` |

## Database tests

| Test |
|---|
| Migration applies cleanly to an empty database |
| Foreign key constraints reject an orphaned insert (e.g., a `chunk` referencing a nonexistent `document_version_id`) |
| `UNIQUE` constraints hold (e.g., duplicate `evidence_code`, duplicate `(document_id, version_number)`) |

## RAG retrieval tests

| Test | Metric |
|---|---|
| Golden query set (see `EVALUATION_PLAN.md`) run against seeded corpus | Recall@5, Recall@10 measured and recorded — not just eyeballed |
| Hybrid retrieval vs. vector-only vs. lexical-only, same query set | Confirms hybrid outperforms either alone on at least the planted paraphrase cases |

## LLM schema tests

| Test |
|---|
| Each of the 4 LLM call types: valid mock response parses correctly into its Pydantic model |
| Each of the 4 LLM call types: malformed mock response triggers the retry path, then the defined failure state after 2nd failure |

## Citation tests

| Test |
|---|
| Citation viewer: clicking a claim's citation returns the exact document/version/page/section it was generated from |
| A citation to a superseded document version still resolves correctly (historical auditability) |

## Claim validation tests

| Test |
|---|
| Worked OVERCLAIM example from `AI_RAG_DESIGN.md` (evidence: "1 of 100 below threshold" / claim: "no contamination detected") classified as `OVERCLAIM` with a non-empty `supported_portion` |
| A claim whose text closely matches its evidence → `SUPPORTED` |

## Contradiction tests

| Test |
|---|
| Two claims about the same product/topic with genuinely conflicting numbers → non-`COMPATIBLE` classification |
| Two claims about the same product/topic but different thresholds/units, non-conflicting → `COMPATIBLE` (this is the deliberate false-positive check — see `EVALUATION_PLAN.md`) |
| Two claims about different `product_topic` → never even reach the LLM call (caught by the deterministic pre-filter) |

## Sufficiency tests

| Test |
|---|
| Seeded "long-term toxicity" query against a corpus containing only short-term studies → `INSUFFICIENT`, gap summary correctly names the missing category |

## E2E tests

One full-path test automating the three killer demo scenarios from
`PROJECT_CONTEXT.md`:

1. Upload documents → ask an answerable query → get a draft with valid
   citations → approve → verify audit log entry.
2. Ask a query whose claim conflicts with a seeded prior approved response →
   verify contradiction surfaces in the response.
3. Ask a query the seeded corpus deliberately can't fully answer → verify
   `INSUFFICIENT` with a correct gap summary.

These three E2E tests are the single highest-priority tests in the entire
suite — they are what get rehearsed for the actual demo, and if they're
automated, the team can re-verify reliability at any point in the 36 hours
without a manual click-through.

## What is explicitly NOT tested (hackathon scope)

- Load/performance testing — out of scope, see `PROJECT_CONTEXT.md` non-goals.
- Cross-browser frontend testing — one target browser (Chrome) is sufficient.
- Full security penetration testing — see `SECURITY.md` for the honest scope
  of what security is and isn't implemented.

# TASKS.md — Execution Backlog

Atomic, agent-sized tasks implementing `IMPLEMENTATION_PLAN.md`. Priority:
P0 = blocker, P1 = must-have, P2 = should-have, P3 = optional/nice-to-have.

Each task below is written small enough for a single coding-agent session —
per `AGENTS.md` task-size guidance ("Build the RAG system" is not a task;
"Implement PDF text extraction preserving page boundaries" is).

---

### TASK-001 — Repository skeleton and Docker Compose
**Priority:** P0 · **Owner:** All (pair on this first) · **Phase:** 0
**Dependencies:** none
**Files:** repo root structure per `ARCHITECTURE.md`, `docker-compose.yml`,
`.env.example`, `.gitignore`
**Description:** Create the directory layout, Docker Compose file with
`db`/`backend`/`frontend` services, and `.env.example` with all variables
from `ENVIRONMENT.md`.
**Acceptance criteria:** `docker compose up` starts all three services
without error.
**Tests:** N/A (infra task) — manual verification of `docker compose up`.
**Status:** not started

### TASK-002 — Initial database migration (all 12 tables)
**Priority:** P0 · **Owner:** Person A · **Phase:** 0
**Dependencies:** TASK-001
**Files:** `backend/alembic/versions/0001_initial_schema.py`,
`backend/app/db.py`, `backend/app/models.py` (SQLAlchemy models mirroring
`DATABASE_SCHEMA.md` exactly)
**Description:** Implement the full schema from `DATABASE_SCHEMA.md` as one
Alembic revision, including the `vector` extension, HNSW index, and GIN
index.
**Acceptance criteria:** Migration applies cleanly to an empty Postgres
instance; all 12 tables exist with correct columns/FKs/indexes.
**Tests:** Migration test (applies without error); FK constraint rejection
test (see `TESTING_STRATEGY.md` database tests).
**Status:** not started

### TASK-003 — FastAPI skeleton + health endpoint
**Priority:** P0 · **Owner:** Person A · **Phase:** 0
**Dependencies:** TASK-001
**Files:** `backend/app/main.py`, `backend/app/config.py` (Settings object)
**Description:** Minimal FastAPI app, `Settings` loaded from environment
variables per `ENVIRONMENT.md`, `GET /api/v1/health` route.
**Acceptance criteria:** `GET /health` returns `200 {"status": "ok"}`.
**Tests:** API test for `/health`.
**Status:** not started

### TASK-004 — Frontend Vite scaffold
**Priority:** P0 · **Owner:** Person C · **Phase:** 0
**Dependencies:** TASK-001
**Files:** `frontend/` full Vite + React + TS + Tailwind scaffold, `api/client.ts` stub
**Description:** Standard Vite React-TS scaffold with Tailwind configured,
one placeholder page confirming it can reach the backend `/health` endpoint.
**Acceptance criteria:** Frontend loads and displays backend health status.
**Tests:** N/A (scaffold task).
**Status:** not started

### TASK-005 — PDF parsing with page preservation
**Priority:** P0 · **Owner:** Person A · **Phase:** 1
**Dependencies:** TASK-002, TASK-003
**Files:** `backend/app/ingestion/parser.py`, `backend/tests/fixtures/sample_3page.pdf`
**Description:** Implement `parse_pdf(file_path) -> list[ParsedPage]` where
`ParsedPage` includes page number and extracted text. Reject unparseable
(scanned/image-only) PDFs with a clear error per `SECURITY.md` file
validation rules.
**Acceptance criteria:** Given the 3-page fixture, returns 3 `ParsedPage`
objects with correct page numbers and non-empty text.
**Tests:** unit test per `TESTING_STRATEGY.md` chunking row.
**Status:** not started

### TASK-006 — Section-aware chunking
**Priority:** P0 · **Owner:** Person A · **Phase:** 1
**Dependencies:** TASK-005
**Files:** `backend/app/ingestion/chunker.py`
**Description:** Implement `chunk(pages: list[ParsedPage]) -> list[Chunk]`,
splitting on detected section/paragraph boundaries, target ~500 tokens per
chunk, preserving `page_start`/`page_end`/`section` per chunk.
**Acceptance criteria:** No chunk splits mid-sentence on the fixture; every
chunk has correct page range.
**Tests:** unit test with known expected chunk boundaries on the fixture.
**Status:** not started

### TASK-007 — Embedding generation + storage
**Priority:** P0 · **Owner:** Person A · **Phase:** 1
**Dependencies:** TASK-006
**Files:** `backend/app/ingestion/embedder.py`
**Description:** Call the configured embedding model per chunk, insert
`chunks` rows (embedding + auto-generated `tsv`), then one `evidence` row
per chunk with a sequentially assigned `evidence_code`.
**Acceptance criteria:** After running, `chunks` and `evidence` tables have
matching row counts with correct foreign keys.
**Tests:** integration test — see `TESTING_STRATEGY.md` ingestion row.
**Status:** not started

### TASK-008 — Document upload endpoints
**Priority:** P0 · **Owner:** Person A · **Phase:** 1
**Dependencies:** TASK-007
**Files:** `backend/app/routers/documents.py`, `schemas.py` (request/response models)
**Description:** Implement `POST /documents`, `POST /documents/{id}/versions`,
`GET /documents`, `GET /documents/{id}` exactly per `API_CONTRACT.md`,
wiring the ingestion pipeline synchronously.
**Acceptance criteria:** All four endpoints match the contract's request/
response shapes exactly; versioning correctly marks prior version
`superseded`.
**Tests:** API tests per `TESTING_STRATEGY.md`.
**Status:** not started

### TASK-009 — Hybrid retrieval (BM25 + HNSW fusion)
**Priority:** P0 · **Owner:** Person A · **Phase:** 2
**Dependencies:** TASK-007
**Files:** `backend/app/retrieval/hybrid_search.py`, `fusion.py`
**Description:** Implement lexical search (`tsvector`/`ts_rank`), vector
search (HNSW cosine distance), and reciprocal rank fusion exactly per the
algorithm in `AI_RAG_DESIGN.md`.
**Acceptance criteria:** Query against seeded fixture corpus returns the
known-relevant chunk in top-5.
**Tests:** unit test for RRF math; integration test against seed corpus.
**Status:** not started

### TASK-010 — Corpus + golden case authoring (ongoing)
**Priority:** P0 · **Owner:** Person C · **Phase:** 3
**Dependencies:** TASK-008 (needs working ingestion to test against)
**Files:** `data/corpus/*`, `data/eval/golden_cases/*.json`
**Description:** Author ~40 synthetic documents (clearly labeled) and the 12
golden evaluation cases per `EVALUATION_PLAN.md`, including the 2 planted
contradiction pairs and the long-term-toxicity gap case.
**Acceptance criteria:** All documents labeled `SYNTHETIC HACKATHON DATA`;
golden case JSON files match the schema in `EVALUATION_PLAN.md`.
**Tests:** N/A directly — validated by tasks that consume this data.
**Status:** not started

### TASK-011 — Requirement extraction (LLM Call 1)
**Priority:** P1 · **Owner:** Person B · **Phase:** 4
**Dependencies:** TASK-003
**Files:** `backend/app/generation/requirement_extraction.py`, Pydantic
schemas per `AI_RAG_DESIGN.md`
**Description:** Implement the LLM call with exact input/output schema,
temperature, retry-once, and whole-query fallback on repeated failure.
**Acceptance criteria:** Given the microbiological safety example query,
produces at least 2 well-formed requirements.
**Tests:** LLM schema tests (mocked valid + malformed responses).
**Status:** not started

### TASK-012 — Response generation with claim/citation proposal (LLM Call 2)
**Priority:** P1 · **Owner:** Person B · **Phase:** 4
**Dependencies:** TASK-009, TASK-011
**Files:** `backend/app/generation/response_generation.py`
**Description:** Implement the call per `AI_RAG_DESIGN.md`, including the
`<UNTRUSTED_EVIDENCE>` wrapping pattern from `SECURITY.md`.
**Acceptance criteria:** Given a seeded evidence pack, produces a valid
`ResponseGenerationOutput` with claims referencing plausible evidence codes.
**Tests:** LLM schema tests; prompt injection test (fixture chunk containing
an injection attempt does not alter model behavior).
**Status:** not started

### TASK-013 — Citation validator
**Priority:** P0 · **Owner:** Person B · **Phase:** 5
**Dependencies:** TASK-007, TASK-012
**Files:** `backend/app/validation/citation_validator.py`
**Description:** Resolve each proposed `evidence_code` against the
`evidence` table; create `citations` rows only for resolved codes; downgrade
claims with zero resolved citations to `UNSUPPORTED` without an LLM call.
**Acceptance criteria:** Mixed valid/invalid proposal produces exactly the
correct citation rows.
**Tests:** per `TESTING_STRATEGY.md` citation validator rows.
**Status:** not started

### TASK-014 — Query pipeline endpoint (orchestration)
**Priority:** P0 · **Owner:** Person B · **Phase:** 4–5
**Dependencies:** TASK-011, TASK-012, TASK-013
**Files:** `backend/app/routers/queries.py`
**Description:** Implement `POST /queries` and `GET /queries/{id}` exactly
per `API_CONTRACT.md`, orchestrating stages 1–7 of the canonical pipeline
(normalization through citation validation).
**Acceptance criteria:** Response shape matches contract exactly.
**Tests:** integration test — full mocked-LLM pipeline run.
**Status:** not started

### TASK-015 — Claim/evidence validation (LLM Call 3)
**Priority:** P1 · **Owner:** Person B · **Phase:** 6
**Dependencies:** TASK-013
**Files:** `backend/app/validation/claim_validator.py`
**Description:** Implement per `AI_RAG_DESIGN.md`, including the
deterministic zero-citation pre-check.
**Acceptance criteria:** The worked overclaim example classifies as
`OVERCLAIM` with a non-empty `supported_portion`.
**Tests:** overclaim + supported worked examples per `TESTING_STRATEGY.md`.
**Status:** not started

### TASK-016 — Sufficiency engine
**Priority:** P1 · **Owner:** Person B · **Phase:** 6
**Dependencies:** TASK-009, TASK-010
**Files:** `backend/app/validation/sufficiency_engine.py`
**Description:** Fully deterministic per-requirement coverage + aggregation
per `AI_RAG_DESIGN.md`. Calibrate `THRESHOLD_HIGH`/`THRESHOLD_LOW` against
real retrieval scores from the seeded corpus.
**Acceptance criteria:** The seeded long-term-toxicity golden case returns
`INSUFFICIENT` with a correct gap summary.
**Tests:** aggregation unit tests (3 cases) + integration test against
golden case.
**Status:** not started

### TASK-017 — Contradiction engine (candidate filter + LLM Call 4)
**Priority:** P1 · **Owner:** Person B (reassign to A if bottlenecked) · **Phase:** 7
**Dependencies:** TASK-010, TASK-015
**Files:** `backend/app/validation/contradiction_engine.py`
**Description:** Deterministic candidate pre-filter (product_topic +
approved status, capped 10) followed by the scoped LLM comparison per
`AI_RAG_DESIGN.md`.
**Acceptance criteria:** Both planted contradiction golden cases caught;
both false-positive-check cases classify `COMPATIBLE`.
**Tests:** per `EVALUATION_PLAN.md` contradiction precision/recall cases.
**Status:** not started

### TASK-018 — Response review endpoints (approve/reject/edit)
**Priority:** P0 · **Owner:** Person A or B · **Phase:** 6–7
**Dependencies:** TASK-014
**Files:** `backend/app/routers/responses.py`
**Description:** Implement `GET/PATCH /responses/{id}`,
`POST /responses/{id}/approve`, `POST /responses/{id}/reject`,
`GET /responses/{id}/audit` per `API_CONTRACT.md`, writing `audit_events`
rows on every state transition.
**Acceptance criteria:** Approval writes correct `audit_events` row; no code
path allows approval without the explicit endpoint call.
**Tests:** API tests per `TESTING_STRATEGY.md`.
**Status:** not started

### TASK-019 — Frontend: Document Library page
**Priority:** P0 · **Owner:** Person C · **Phase:** 8
**Dependencies:** TASK-004; can start against mocked API before TASK-008 lands
**Files:** `frontend/src/pages/Library.tsx`
**Description:** Upload form, document list, version history display.
**Acceptance criteria:** Uploading a PDF (real or mocked backend) shows it
in the list with correct metadata.
**Tests:** component test against mocked API response.
**Status:** not started

### TASK-020 — Frontend: Query Workspace page
**Priority:** P0 · **Owner:** Person C · **Phase:** 8
**Dependencies:** TASK-004; mock-first
**Files:** `frontend/src/pages/Workspace.tsx`,
`components/CitationChip.tsx`, `components/ClaimList.tsx`
**Description:** Query input box, draft display with claims and clickable
citation chips (opens evidence detail).
**Acceptance criteria:** Submitting a query (real or mocked) displays draft
text with visible, clickable citations.
**Tests:** component test against mocked response shape.
**Status:** not started

### TASK-021 — Frontend: Contradiction panel + Gap map
**Priority:** P1 · **Owner:** Person C · **Phase:** 9
**Dependencies:** TASK-020, TASK-016, TASK-017 for real data
**Files:** `frontend/src/components/ContradictionPanel.tsx`, `GapMap.tsx`
**Description:** Side-by-side claim comparison for contradictions; a clear
missing/covered requirement list for the gap map.
**Acceptance criteria:** Both are visually distinct, clear panels — not
buried inline — since these are two of the three killer demo moments.
**Tests:** component tests against fixture data matching golden cases.
**Status:** not started

### TASK-022 — Frontend: Review + Audit trail
**Priority:** P0 · **Owner:** Person C · **Phase:** 9
**Dependencies:** TASK-018, TASK-020
**Files:** `frontend/src/pages/Review.tsx`, `components/AuditTrail.tsx`
**Description:** Approve/edit/reject controls, expandable audit event list.
**Acceptance criteria:** Approving a response updates its status visibly
and an audit event appears.
**Tests:** component test with mocked approve action.
**Status:** not started

### TASK-023 — Full integration pass
**Priority:** P0 · **Owner:** All · **Phase:** 10
**Dependencies:** all prior P0/P1 tasks
**Files:** N/A (integration, not new files)
**Description:** Remove all frontend mocks, wire fully to the real backend,
run the three E2E demo scenarios repeatedly.
**Acceptance criteria:** all three E2E tests from `TESTING_STRATEGY.md` pass
reliably (5 consecutive runs).
**Tests:** the three E2E tests + the eval script from `EVALUATION_PLAN.md`.
**Status:** not started

### TASK-024 — Demo hardening
**Priority:** P0 · **Owner:** All · **Phase:** 11
**Dependencies:** TASK-023
**Files:** N/A
**Description:** UI polish, error/loading states, 10+ rehearsals, backup
video, DB snapshot, `demo-final` tag.
**Acceptance criteria:** the three killer demo moments work across 5+
consecutive rehearsals.
**Tests:** N/A (rehearsal, not automated).
**Status:** not started

---

## P2/P3 tasks (should-have / optional — pick up only if ahead of schedule)

| ID | Title | Priority | Dependencies | Files |
|---|---|---|---|---|
| TASK-025 | Cross-encoder reranking pass | P2 | TASK-009 | `retrieval/rerank.py` |
| TASK-026 | Evaluation script (`run_eval.py`) automating `EVALUATION_PLAN.md` | P2 | TASK-010, TASK-023 | `scripts/run_eval.py` |
| TASK-027 | Full document-versioning frontend (live re-upload demo) | P2 | TASK-019 | `Library.tsx` extension |
| TASK-028 | GitHub Actions CI (lint + test on PR) | P3 | TASK-001 | `.github/workflows/ci.yml` |
| TASK-029 | Extend golden case set beyond the minimum 12 | P3 | TASK-010 | `data/eval/golden_cases/*` |

**Cut order if time runs out:** TASK-028 first, then TASK-025, then TASK-027.
TASK-026 should be kept if at all possible — a measured eval result is cheap
insurance against an unanswerable judge question.

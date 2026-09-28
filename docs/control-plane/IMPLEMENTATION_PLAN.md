# IMPLEMENTATION_PLAN.md — Phase-by-Phase Build Plan

This is the execution sequence. Each phase lists prerequisites, files touched,
database/API changes, tests, acceptance criteria, and failure/recovery
behavior. `TASKS.md` breaks these phases into atomic, agent-sized tickets —
this file is the phase-level map that `TASKS.md` implements against.

## Phase 0 — Repository + Infrastructure (Hour 0–4)

**Objective:** every developer can run `docker compose up` and reach a working
skeleton (empty DB with schema applied, backend returns `200` on `/health`,
frontend loads a blank page hitting the backend).

**Prerequisites:** none.
**Files created:** full repo skeleton per `ARCHITECTURE.md` directory layout,
`docker-compose.yml`, `.env.example`, initial Alembic setup, `backend/app/main.py`
with a `/health` route, `frontend` Vite scaffold.
**Database changes:** initial migration creating all 12 tables from
`DATABASE_SCHEMA.md` in one revision.
**API changes:** `GET /health` only.
**Tests:** migration applies cleanly to an empty DB; `/health` returns `200`.
**Acceptance criteria:** all three developers have run `docker compose up`
successfully and confirmed `/health` responds.
**Failure mode:** Docker networking/dependency issues. **Recovery:** fall back
to running Postgres locally (not in Docker) for whoever is blocked, backend
`DATABASE_URL` pointed at localhost — do not let infrastructure block feature
work past hour 2.

## Phase 1 — Document Ingestion (Hour 4–10) — Person A

**Objective:** upload a PDF, get it parsed, chunked, embedded, and stored with
correct provenance.
**Prerequisites:** Phase 0 complete.
**Files:** `backend/app/ingestion/parser.py`, `chunker.py`, `embedder.py`,
`routers/documents.py`.
**Database changes:** none beyond Phase 0 (schema already covers this).
**API changes:** `POST /documents`, `POST /documents/{id}/versions`,
`GET /documents`, `GET /documents/{id}` per `API_CONTRACT.md`.
**Tests:** unit tests for chunking (page preservation), integration test for
full upload → DB row verification (see `TESTING_STRATEGY.md`).
**Acceptance criteria:** uploading a 3-page fixture PDF produces correct
`document_versions`, `chunks` (with page numbers), and `evidence` rows.
**Failure mode:** embedding API failures. **Recovery:** retry once, then fail
the whole upload cleanly (no partial ingestion, per `RULES.md`).

## Phase 2 — Hybrid Retrieval (Hour 4–10, parallel with Phase 1) — Person A

**Objective:** given a search string, return ranked candidate chunks via
fused BM25 + HNSW vector search.
**Prerequisites:** Phase 1's chunks/embeddings exist (can develop against
seed fixtures before Phase 1 fully lands).
**Files:** `backend/app/retrieval/hybrid_search.py`, `fusion.py`.
**Database changes:** confirm HNSW and GIN indexes are created (already in
Phase 0 migration).
**API changes:** none yet (retrieval is called internally, not exposed
directly).
**Tests:** RRF fusion unit test against a known fixture; retrieval integration
test against seeded corpus.
**Acceptance criteria:** a query for a known topic returns the expected
fixture chunk within top-5.

## Phase 3 — Corpus + Golden Cases (Hour 4–16, ongoing) — Person C

**Objective:** author the ~40-document synthetic corpus, including the
planted contradiction pairs, the evidence-gap case, and the 12 golden
evaluation cases from `EVALUATION_PLAN.md`.
**Prerequisites:** Phase 1 must be functional enough to actually ingest these
documents once written.
**Files:** `data/corpus/*.pdf` (or `.txt` converted to PDF), `data/eval/golden_cases/*.json`.
**Tests:** N/A directly — this data feeds Phase 6+ tests.
**Acceptance criteria:** corpus is labeled `SYNTHETIC HACKATHON DATA`
throughout, contains at minimum 2 genuine contradiction pairs and 1 clean
evidence gap (long-term toxicity absent), all golden cases are written.

## Phase 4 — Requirement Extraction + Response Generation (Hour 10–16) — Person B

**Objective:** LLM Calls 1 and 2 from `AI_RAG_DESIGN.md` implemented, schema-
validated, with retry/failure states.
**Prerequisites:** Phase 2's retrieval callable.
**Files:** `backend/app/generation/requirement_extraction.py`,
`response_generation.py`, `schemas.py` (Pydantic models for both calls).
**Database changes:** none beyond Phase 0.
**Tests:** LLM schema tests with mocked responses (valid + malformed) for
both calls.
**Acceptance criteria:** given a query and a seeded evidence pack, produces a
valid `ResponseGenerationOutput` with claims and proposed citations.

## Phase 5 — Citation Validation (Hour 10–16, parallel) — Person B

**Objective:** deterministic resolution of proposed evidence codes into real
`citations` rows.
**Prerequisites:** Phase 1 (evidence exists), Phase 4 (proposals exist).
**Files:** `backend/app/validation/citation_validator.py`.
**Database changes:** none beyond Phase 0.
**Tests:** valid code → citation created; invalid code → no citation created,
claim flagged (see `TESTING_STRATEGY.md`).
**Acceptance criteria:** a mixed valid/invalid citation proposal produces
exactly the correct citation rows, no more, no less.

**HOUR 16 CHECKPOINT (all three): merge to `main`, run the full pipeline
once — upload → query → draft with citations → something visible end to
end, even if ugly. This is mandatory, not optional. Catching a break here is
recoverable; catching it at hour 30 is not.**

## Phase 6 — Claim/Evidence Validation + Sufficiency Engine (Hour 16–22) — Person B

**Objective:** LLM Call 3 (claim validation) and the fully deterministic
sufficiency engine implemented.
**Prerequisites:** Phase 5.
**Files:** `backend/app/validation/claim_validator.py`,
`sufficiency_engine.py`.
**Database changes:** none beyond Phase 0.
**Tests:** overclaim worked example, sufficiency aggregation unit tests
(all three coverage-combination cases), insufficient-evidence integration
test against the seeded gap case.
**Acceptance criteria:** the seeded long-term-toxicity case returns
`INSUFFICIENT` with a correct gap summary; the overclaim case classifies
correctly.

## Phase 7 — Contradiction Engine (Hour 16–22, parallel) — Person B (or A if
Person B is bottlenecked — this is the one phase worth reassigning if
behind schedule, since it's demo-critical)

**Objective:** LLM Call 4 plus deterministic candidate pre-filter.
**Prerequisites:** Phase 6 (approved responses/claims need to exist to test
against — use seed data for approved historical responses).
**Files:** `backend/app/validation/contradiction_engine.py`.
**Database changes:** none beyond Phase 0.
**Tests:** true-positive and false-positive-check cases from
`EVALUATION_PLAN.md`.
**Acceptance criteria:** both planted contradiction pairs are caught; both
false-positive-check pairs classify `COMPATIBLE`.

## Phase 8 — Frontend: Library + Query Workspace (Hour 4–16) — Person C

**Objective:** document upload UI, query input, draft display with citations
visible.
**Prerequisites:** `API_CONTRACT.md` shapes agreed (Phase 0); can build
against mocked JSON before backend phases land.
**Files:** `frontend/src/pages/Library.tsx`, `Workspace.tsx`,
`components/CitationChip.tsx`, `api/client.ts`.
**Tests:** component-level tests for rendering a mocked response shape
correctly.
**Acceptance criteria:** uploading a document and submitting a query
(against mocked or real backend) displays a draft with clickable citations.

## Phase 9 — Frontend: Contradiction + Sufficiency + Review (Hour 16–28) — Person C

**Objective:** contradiction panel, gap map, approve/edit/reject controls,
audit trail display.
**Prerequisites:** Phase 8, backend Phases 6–7 for real data.
**Files:** `frontend/src/pages/Review.tsx`,
`components/ContradictionPanel.tsx`, `GapMap.tsx`, `AuditTrail.tsx`.
**Tests:** component tests for each panel against known fixture data.
**Acceptance criteria:** all three killer demo moments are visibly
representable in the UI, not just present in API responses.

## Phase 10 — Full Integration (Hour 28–32) — All three

**Objective:** every layer wired together against the real backend, no mocks
remaining, full pipeline runs reliably multiple times in a row.
**Prerequisites:** all prior phases.
**Tests:** run all three E2E demo-scenario tests from `TESTING_STRATEGY.md`.
Run the eval script from `EVALUATION_PLAN.md`.
**Acceptance criteria:** all three E2E tests pass; eval metrics meet the
"success" thresholds in `EVALUATION_PLAN.md`.
**Failure mode:** something breaks under real integration that worked
against mocks. **Recovery:** this is exactly why the hour-16 checkpoint
exists — the gap between mock and real behavior should already be mostly
closed by this point; treat any surprise here as high priority, cut
should-have features (reranking, full versioning UI) before cutting demo
reliability.

## Phase 11 — Demo Hardening (Hour 32–36) — All three

**Objective:** polish, rehearse, prepare fallbacks.
**Tasks:** UI polish and loading/error states; 10+ full demo run-throughs;
record a backup demo video in case of live failure; snapshot the demo
database state (`pg_dump`) so it can be restored instantly if corrupted
during rehearsal; tag the final commit `demo-final` per `GIT_WORKFLOW.md`;
prepare answers to the judge-attack questions the team anticipates.
**Acceptance criteria:** the three killer demo moments each work reliably
across at least 5 consecutive rehearsal runs.

## Priority classification (referenced throughout)

- **MUST HAVE:** Phases 0, 1, 2, 4, 5, 6 (sufficiency + overclaim), 7
  (contradiction), 8, 9 (review + audit), 10, 11.
- **SHOULD HAVE:** reranking (inside Phase 2), full document versioning UI
  (inside Phase 9), evaluation harness beyond the minimum 12 cases.
- **NICE TO HAVE:** CI/CD, real auth/RBAC beyond the static token.
- **CUT IF BEHIND:** CI/CD (first cut), reranking (second cut — hybrid
  retrieval alone still works), full versioning UI (third cut — keep the
  schema/backend support, simplify the frontend to not demo re-upload live).

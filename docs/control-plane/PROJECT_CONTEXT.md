# PROJECT_CONTEXT.md — Everything a Fresh Session Needs to Know

Read this file first in any new session. It gives you the "why" without
requiring you to read a full conversation history.

## The event

YUVA Mega-Thon, BioTech track, problem statement **PS-7**, company partner
**Biokraft Foods Private Limited**. Team "BigPotatoes" was shortlisted by
industry judges for the 36-hour final build. Team of 3 active developers.
Build window: Monday 9:30 PM to Wednesday 9:30 AM.

## The problem, in one paragraph

A novel-food company (like a cultivated-meat producer) preparing a regulatory
submission has to answer detailed regulator questions with evidence-backed,
precisely cited responses — across many rounds, over months or years — without
ever contradicting something they said in an earlier round, and without ever
claiming more than their evidence actually supports. Doing this by hand across
a huge, growing document set is slow and error-prone; a single accidental
inconsistency can trigger new rounds of regulator questions and delay approval.

## The product

**ReguLens** — "Evidence-grounded regulatory responses, built for
auditability." It is not a chatbot. It is a regulatory-response engineering
workspace: retrieve real evidence, draft a response, validate every citation
against real stored sources, check the new response against everything
submitted before, and explicitly say when the available evidence isn't enough
— then hand the whole thing to a human for approval. The system never decides
whether a product is safe and never auto-submits anything.

## Primary user

A Regulatory Affairs Specialist assembling evidence-backed responses to
regulator queries across multi-round submissions.

## The philosophy that drives every design decision

**Evidence → Claim → Citation → Consistency → Human Approval.**
Not: PDF → LLM → Answer.

The governing rule: **LLM proposes, backend validates, PostgreSQL becomes
truth.** See `RULES.md` rule #1–2 for the exact wording; every architectural
choice traces back to this.

## MVP boundary

**In scope:** document upload/ingestion, a regulator-query workspace, hybrid
retrieval, LLM-drafted responses with validated citations, claim/evidence
validation, contradiction detection against prior approved responses, evidence
sufficiency scoring with a gap map, human review (approve/edit/reject), and a
basic audit trail.

**Out of scope for this hackathon:** OCR for scanned PDFs, enterprise-grade
RBAC/multi-tenant auth, figure/table image analysis, autonomous submission to
a regulator, any multi-agent/autonomous-reasoning architecture, full
multi-response dossier assembly beyond exporting a single approved response,
CI/CD pipelines (cut if time-constrained).

## The three killer demo moments

These are the actual differentiators judges need to see, live, not just hear
described:

1. **A hallucinated/invalid citation caught before it reaches a human.** Proves
   the system isn't "just an LLM that seems careful."
2. **A genuine planted contradiction** between a new draft claim and a
   previously approved response, caught and explained with both claims shown
   side by side and the reasoning visible.
3. **A genuine INSUFFICIENT_EVIDENCE result** with a clean gap map — the
   system refusing to fabricate a conclusion the corpus doesn't support.

If these three work reliably, the demo succeeds regardless of anything else.

## Data

~40 synthetic documents, all explicitly labeled as synthetic hackathon data —
scientific-paper-style text, mock internal study reports, mock prior
regulatory responses, and public regulatory guidance references (SFA
Singapore, EFSA EU, FSANZ Australia/NZ, FSA UK, FSSAI India). No real
proprietary Biokraft data is used or invented. The corpus deliberately
contains 2–3 planted contradiction pairs and at least one deliberate evidence
gap (e.g., no long-term toxicity study present) to make the three demo moments
reliably reproducible.

## Approved technology stack

Frontend: React + TypeScript + Vite + Tailwind CSS.
Backend: Python + FastAPI.
Database: PostgreSQL + pgvector (single database — no additional data stores).
Retrieval: hybrid BM25 (Postgres full-text search) + vector search (pgvector
HNSW index), optional reranking pass.
LLM: Anthropic Claude, structured JSON output, validated via Pydantic on every
call.
Infrastructure: Docker / Docker Compose. No Kafka, no Redis, no Kubernetes, no
Neo4j, no Celery, no microservices split. Every one of these was deliberately
excluded because the problem at this scale does not need them — see
`ARCHITECTURE.md` for the reasoning.

## Team

3 active developers, split by architectural layer (not by feature) to avoid
blocking each other:
- **Person A** — Ingestion + Retrieval
- **Person B** — Generation + Validation engines (claims, citations,
  contradiction, sufficiency)
- **Person C** — Frontend + integration + demo/corpus authoring

## Non-goals — say this explicitly if asked

ReguLens does not certify regulatory compliance, does not determine whether a
product is scientifically safe, and is not a production system. It is a
prototype demonstrating an evidence-engineering architecture that could
plausibly evolve toward production. This is stated deliberately and should
never be contradicted by anything in the UI or documentation.

## Where to go next

- Full technical architecture and query lifecycle: `ARCHITECTURE.md`
- Database schema: `DATABASE_SCHEMA.md`
- API shapes: `API_CONTRACT.md`
- Exact LLM call contracts: `AI_RAG_DESIGN.md`
- What to build and in what order: `IMPLEMENTATION_PLAN.md` and `TASKS.md`

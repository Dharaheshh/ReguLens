# DATABASE_SCHEMA.md — Approved PostgreSQL Schema

This is the complete, approved schema. Twelve tables. Do not add, remove, or
rename a table or column without updating this file first — see `RULES.md`
database rules.

All schema changes go through Alembic migrations. No manual DDL against a
running database at any point, including local development.

```sql
CREATE EXTENSION IF NOT EXISTS "pgcrypto";  -- for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS vector;       -- pgvector
```

## documents

Represents one uploaded logical document (may have multiple versions).

```sql
CREATE TABLE documents (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename            TEXT NOT NULL,
    doc_type            TEXT NOT NULL,   -- 'scientific_paper' | 'regulatory_guidance'
                                          -- | 'internal_study' | 'prior_response'
    jurisdiction        TEXT,            -- 'SFA' | 'EFSA' | 'FSANZ' | 'FSA' | 'FSSAI' | NULL
    is_synthetic        BOOLEAN NOT NULL DEFAULT TRUE,
    current_version_id  UUID,            -- FK to document_versions.id, set after first version insert
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**Purpose:** the stable identity of a document across re-uploads.
**Relationships:** has many `document_versions`. `current_version_id` points to
the latest non-superseded version.

## document_versions

Each upload/re-upload of a document.

```sql
CREATE TABLE document_versions (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id   UUID NOT NULL REFERENCES documents(id),
    version_number INT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'current',  -- 'current' | 'superseded'
    file_path     TEXT NOT NULL,
    uploaded_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (document_id, version_number)
);
CREATE INDEX idx_document_versions_document_id ON document_versions(document_id);
```

**Purpose:** immutable record of each version. Never deleted — status flips to
`superseded` on re-upload of a newer version.
**Relationships:** belongs to `documents`; has many `chunks`.

## chunks

A parsed, chunked, embedded piece of a specific document version.

```sql
CREATE TABLE chunks (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_version_id UUID NOT NULL REFERENCES document_versions(id),
    section             TEXT,
    page_start          INT,
    page_end            INT,
    content             TEXT NOT NULL,
    embedding           VECTOR(1536),   -- dimension must match embedding model in ENVIRONMENT.md
    tsv                 TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_chunks_embedding_hnsw ON chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_chunks_tsv_gin ON chunks USING GIN (tsv);
CREATE INDEX idx_chunks_document_version_id ON chunks(document_version_id);
```

**Purpose:** the actual searchable text unit, with the two indexes that power
hybrid retrieval (HNSW for semantic, GIN on `tsv` for lexical/BM25-style
search).
**Relationships:** belongs to `document_versions`; has one `evidence` row
(1:1, see below).

## evidence

A citable projection of a chunk, created once at ingestion. Not a duplicate
store of the text — it's the object citations point to, carrying
citation-relevant metadata.

```sql
CREATE TABLE evidence (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evidence_code       TEXT NOT NULL UNIQUE,  -- e.g. 'EVD-01872' — what the LLM cites by
    chunk_id            UUID NOT NULL REFERENCES chunks(id),
    document_id         UUID NOT NULL REFERENCES documents(id),       -- denormalized for fast lookup
    document_version_id UUID NOT NULL REFERENCES document_versions(id),
    source_type         TEXT NOT NULL,   -- mirrors documents.doc_type at creation time
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_evidence_code ON evidence(evidence_code);
CREATE INDEX idx_evidence_chunk_id ON evidence(chunk_id);
```

**Purpose:** the stable, citable object. `evidence_code` is what an LLM sees
and proposes in a citation; the backend resolves it against this table.
**Relationships:** belongs to `chunks` (1:1), `documents`, `document_versions`.

## regulatory_queries

A regulator question entered into the system.

```sql
CREATE TABLE regulatory_queries (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_text   TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**Purpose:** the entry point of the pipeline.
**Relationships:** has many `requirements`; has one `responses` row (per
attempt — a query can be re-run, producing a new response).

## requirements

A single checkable requirement extracted from a regulatory query.

```sql
CREATE TABLE requirements (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id     UUID NOT NULL REFERENCES regulatory_queries(id),
    req_code     TEXT NOT NULL,   -- e.g. 'REQ-01', unique within a query
    description  TEXT NOT NULL,
    keywords     TEXT[],
    status       TEXT NOT NULL DEFAULT 'pending',  -- 'COVERED' | 'PARTIALLY_COVERED' | 'NOT_COVERED'
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (query_id, req_code)
);
```

**Purpose:** makes "is there enough evidence" concrete and checkable per
sub-question, rather than one vague judgment over the whole query.
**Relationships:** belongs to `regulatory_queries`; has many
`requirement_evidence` rows.

## requirement_evidence

Join table: which evidence was retrieved for which requirement, and how
relevant it scored, for this specific query.

```sql
CREATE TABLE requirement_evidence (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requirement_id  UUID NOT NULL REFERENCES requirements(id),
    evidence_id     UUID NOT NULL REFERENCES evidence(id),
    retrieval_score FLOAT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (requirement_id, evidence_id)
);
CREATE INDEX idx_req_evidence_requirement_id ON requirement_evidence(requirement_id);
```

**Purpose:** this is where per-query, retrieval-time relevance data lives, so
that `evidence` itself can stay stable and reusable across many queries. Also
this table's rows are exactly what the sufficiency engine aggregates over.

## responses

A drafted (and eventually reviewed) response to a query.

```sql
CREATE TABLE responses (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id            UUID NOT NULL REFERENCES regulatory_queries(id),
    draft_text          TEXT,
    sufficiency_status  TEXT,    -- 'SUFFICIENT' | 'PARTIALLY_SUFFICIENT' | 'INSUFFICIENT'
    gap_summary         TEXT,
    status              TEXT NOT NULL DEFAULT 'draft',  -- 'draft' | 'approved' | 'rejected'
    version             INT NOT NULL DEFAULT 1,
    reviewed_by         TEXT,
    reviewed_at         TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_responses_query_id ON responses(query_id);
```

**Purpose:** the draft/reviewed object at the center of the human review
screen.
**Relationships:** belongs to `regulatory_queries`; has many `claims`.

## claims

An individual factual statement extracted from a response draft.

```sql
CREATE TABLE claims (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    response_id       UUID NOT NULL REFERENCES responses(id),
    claim_code        TEXT NOT NULL,   -- e.g. 'CLM-0042'
    claim_text        TEXT NOT NULL,
    product_topic     TEXT NOT NULL,   -- used to scope contradiction candidate matching
    validation_state  TEXT,   -- 'SUPPORTED' | 'PARTIALLY_SUPPORTED' | 'UNSUPPORTED' | 'OVERCLAIM'
    validation_reasoning TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_claims_response_id ON claims(response_id);
CREATE INDEX idx_claims_product_topic ON claims(product_topic);
```

**Purpose:** the unit that citations attach to and that contradiction
detection compares across responses.
**Relationships:** belongs to `responses`; has many `citations`; referenced by
`contradictions` (as either claim_a or claim_b).

## citations

Links a validated claim to a validated piece of evidence.

```sql
CREATE TABLE citations (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id     UUID NOT NULL REFERENCES claims(id),
    evidence_id  UUID NOT NULL REFERENCES evidence(id),
    validated    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_citations_claim_id ON citations(claim_id);
```

**Purpose:** this row only exists once the backend has confirmed
`evidence_id` is real — see `RULES.md` rule #3–4. A claim with a proposed but
unresolved evidence ID never gets a row here.
**Relationships:** belongs to `claims` and `evidence`.

## contradictions

A flagged relationship between a new claim and a historical claim.

```sql
CREATE TABLE contradictions (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_a_id    UUID NOT NULL REFERENCES claims(id),
    claim_b_id    UUID NOT NULL REFERENCES claims(id),
    classification TEXT NOT NULL,  -- 'POTENTIAL_CONTRADICTION' | 'LIKELY_CONTRADICTION'
                                    -- | 'INSUFFICIENT_CONTEXT'  ('COMPATIBLE' is not stored)
    reasoning     TEXT NOT NULL,
    resolved      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_contradictions_claim_a ON contradictions(claim_a_id);
CREATE INDEX idx_contradictions_claim_b ON contradictions(claim_b_id);
```

**Purpose:** the object the contradiction panel in the UI reads from.
`COMPATIBLE` classifications are not stored — only pairs that need human
attention.
**Relationships:** references two `claims` rows.

## audit_events

Immutable log of every state-changing action.

```sql
CREATE TABLE audit_events (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type   TEXT NOT NULL,   -- e.g. 'response_approved', 'response_rejected', 'llm_call_failed'
    response_id  UUID REFERENCES responses(id),
    actor        TEXT NOT NULL,   -- reviewer identifier, or 'system'
    payload      JSONB,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_audit_events_response_id ON audit_events(response_id);
```

**Purpose:** every human approval, rejection, and every system-level failure
state is recorded here, permanently. This table is append-only — rows are
never updated or deleted.
**Relationships:** optionally references `responses`.

## Object chain reference

```
Document → DocumentVersion → Chunk → Evidence
                                          ↓
RegulatoryQuery → Requirement → RequirementEvidence (links Requirement ↔ Evidence)
                                          ↓
                                       Response → Claim → Citation (links Claim ↔ Evidence)
                                                     ↓
                                              Contradiction (links Claim ↔ Claim)
```

## Migration rules

- Every schema change is a new Alembic revision file, never a hand-applied
  `ALTER TABLE`.
- Migrations are reviewed against this document before being written —
  this file is updated first if the schema itself is changing (which requires
  sign-off per `AGENTS.md` decision hierarchy, not an agent's unilateral
  choice).
- Seed data (the ~40 synthetic documents, planted contradiction/gap cases) is
  loaded via a separate seed script, never baked into a migration.

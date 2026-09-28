"""initial_schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-09-28 22:49:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')
    op.execute('CREATE EXTENSION IF NOT EXISTS vector;')

    op.execute('''
    CREATE TABLE documents (
        id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        filename            TEXT NOT NULL,
        doc_type            TEXT NOT NULL,
        jurisdiction        TEXT,
        is_synthetic        BOOLEAN NOT NULL DEFAULT TRUE,
        current_version_id  UUID,
        created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    ''')

    op.execute('''
    CREATE TABLE document_versions (
        id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        document_id   UUID NOT NULL REFERENCES documents(id),
        version_number INT NOT NULL,
        status        TEXT NOT NULL DEFAULT 'current',
        file_path     TEXT NOT NULL,
        uploaded_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
        UNIQUE (document_id, version_number)
    );
    CREATE INDEX idx_document_versions_document_id ON document_versions(document_id);
    ''')

    op.execute('''
    CREATE TABLE chunks (
        id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        document_version_id UUID NOT NULL REFERENCES document_versions(id),
        section             TEXT,
        page_start          INT,
        page_end            INT,
        content             TEXT NOT NULL,
        embedding           VECTOR(384),
        tsv                 TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
        created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX idx_chunks_embedding_hnsw ON chunks USING hnsw (embedding vector_cosine_ops);
    CREATE INDEX idx_chunks_tsv_gin ON chunks USING GIN (tsv);
    CREATE INDEX idx_chunks_document_version_id ON chunks(document_version_id);
    ''')

    op.execute('''
    CREATE TABLE evidence (
        id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        evidence_code       TEXT NOT NULL UNIQUE,
        chunk_id            UUID NOT NULL REFERENCES chunks(id),
        document_id         UUID NOT NULL REFERENCES documents(id),
        document_version_id UUID NOT NULL REFERENCES document_versions(id),
        source_type         TEXT NOT NULL,
        created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX idx_evidence_code ON evidence(evidence_code);
    CREATE INDEX idx_evidence_chunk_id ON evidence(chunk_id);
    ''')

    op.execute('''
    CREATE TABLE regulatory_queries (
        id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        query_text   TEXT NOT NULL,
        created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    ''')

    op.execute('''
    CREATE TABLE requirements (
        id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        query_id     UUID NOT NULL REFERENCES regulatory_queries(id),
        req_code     TEXT NOT NULL,
        description  TEXT NOT NULL,
        keywords     TEXT[],
        status       TEXT NOT NULL DEFAULT 'pending',
        created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
        UNIQUE (query_id, req_code)
    );
    ''')

    op.execute('''
    CREATE TABLE requirement_evidence (
        id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        requirement_id  UUID NOT NULL REFERENCES requirements(id),
        evidence_id     UUID NOT NULL REFERENCES evidence(id),
        retrieval_score FLOAT NOT NULL,
        created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
        UNIQUE (requirement_id, evidence_id)
    );
    CREATE INDEX idx_req_evidence_requirement_id ON requirement_evidence(requirement_id);
    ''')

    op.execute('''
    CREATE TABLE responses (
        id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        query_id            UUID NOT NULL REFERENCES regulatory_queries(id),
        draft_text          TEXT,
        sufficiency_status  TEXT,
        gap_summary         TEXT,
        status              TEXT NOT NULL DEFAULT 'draft',
        version             INT NOT NULL DEFAULT 1,
        reviewed_by         TEXT,
        reviewed_at         TIMESTAMPTZ,
        created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX idx_responses_query_id ON responses(query_id);
    ''')

    op.execute('''
    CREATE TABLE claims (
        id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        response_id       UUID NOT NULL REFERENCES responses(id),
        claim_code        TEXT NOT NULL,
        claim_text        TEXT NOT NULL,
        product_topic     TEXT NOT NULL,
        validation_state  TEXT,
        validation_reasoning TEXT,
        created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX idx_claims_response_id ON claims(response_id);
    CREATE INDEX idx_claims_product_topic ON claims(product_topic);
    ''')

    op.execute('''
    CREATE TABLE citations (
        id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        claim_id     UUID NOT NULL REFERENCES claims(id),
        evidence_id  UUID NOT NULL REFERENCES evidence(id),
        validated    BOOLEAN NOT NULL DEFAULT FALSE,
        created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX idx_citations_claim_id ON citations(claim_id);
    ''')

    op.execute('''
    CREATE TABLE contradictions (
        id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        claim_a_id    UUID NOT NULL REFERENCES claims(id),
        claim_b_id    UUID NOT NULL REFERENCES claims(id),
        classification TEXT NOT NULL,
        reasoning     TEXT NOT NULL,
        resolved      BOOLEAN NOT NULL DEFAULT FALSE,
        created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX idx_contradictions_claim_a ON contradictions(claim_a_id);
    CREATE INDEX idx_contradictions_claim_b ON contradictions(claim_b_id);
    ''')

    op.execute('''
    CREATE TABLE audit_events (
        id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        event_type   TEXT NOT NULL,
        response_id  UUID REFERENCES responses(id),
        actor        TEXT NOT NULL,
        payload      JSONB,
        created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX idx_audit_events_response_id ON audit_events(response_id);
    ''')

def downgrade() -> None:
    op.execute('DROP TABLE IF EXISTS audit_events CASCADE;')
    op.execute('DROP TABLE IF EXISTS contradictions CASCADE;')
    op.execute('DROP TABLE IF EXISTS citations CASCADE;')
    op.execute('DROP TABLE IF EXISTS claims CASCADE;')
    op.execute('DROP TABLE IF EXISTS responses CASCADE;')
    op.execute('DROP TABLE IF EXISTS requirement_evidence CASCADE;')
    op.execute('DROP TABLE IF EXISTS requirements CASCADE;')
    op.execute('DROP TABLE IF EXISTS regulatory_queries CASCADE;')
    op.execute('DROP TABLE IF EXISTS evidence CASCADE;')
    op.execute('DROP TABLE IF EXISTS chunks CASCADE;')
    op.execute('DROP TABLE IF EXISTS document_versions CASCADE;')
    op.execute('DROP TABLE IF EXISTS documents CASCADE;')
    op.execute('DROP EXTENSION IF EXISTS vector;')
    op.execute('DROP EXTENSION IF EXISTS "pgcrypto";')

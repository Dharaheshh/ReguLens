import uuid
from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, Index, Text, UniqueConstraint, ARRAY
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR, JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from sqlalchemy.sql import text
from sqlalchemy.sql.sqltypes import TIMESTAMP

from app.db import Base

class Document(Base):
    __tablename__ = "documents"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    filename = Column(Text, nullable=False)
    doc_type = Column(Text, nullable=False)
    jurisdiction = Column(Text, nullable=True)
    is_synthetic = Column(Boolean, nullable=False, server_default=text("TRUE"))
    current_version_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

class DocumentVersion(Base):
    __tablename__ = "document_versions"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    status = Column(Text, nullable=False, server_default=text("'current'"))
    file_path = Column(Text, nullable=False)
    uploaded_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    __table_args__ = (
        UniqueConstraint("document_id", "version_number"),
        Index("idx_document_versions_document_id", "document_id"),
    )

class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    document_version_id = Column(UUID(as_uuid=True), ForeignKey("document_versions.id"), nullable=False)
    section = Column(Text, nullable=True)
    page_start = Column(Integer, nullable=True)
    page_end = Column(Integer, nullable=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(384))
    tsv = Column(TSVECTOR, server_default=text("to_tsvector('english', content)"))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    __table_args__ = (
        Index("idx_chunks_embedding_hnsw", "embedding", postgresql_using="hnsw", postgresql_ops={"embedding": "vector_cosine_ops"}),
        Index("idx_chunks_tsv_gin", "tsv", postgresql_using="gin"),
        Index("idx_chunks_document_version_id", "document_version_id"),
    )

class Evidence(Base):
    __tablename__ = "evidence"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    evidence_code = Column(Text, nullable=False, unique=True)
    chunk_id = Column(UUID(as_uuid=True), ForeignKey("chunks.id"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    document_version_id = Column(UUID(as_uuid=True), ForeignKey("document_versions.id"), nullable=False)
    source_type = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    __table_args__ = (
        Index("idx_evidence_code", "evidence_code"),
        Index("idx_evidence_chunk_id", "chunk_id"),
    )

class RegulatoryQuery(Base):
    __tablename__ = "regulatory_queries"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    query_text = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

class Requirement(Base):
    __tablename__ = "requirements"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    query_id = Column(UUID(as_uuid=True), ForeignKey("regulatory_queries.id"), nullable=False)
    req_code = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    keywords = Column(ARRAY(Text))
    status = Column(Text, nullable=False, server_default=text("'pending'"))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    __table_args__ = (
        UniqueConstraint("query_id", "req_code"),
    )

class RequirementEvidence(Base):
    __tablename__ = "requirement_evidence"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    requirement_id = Column(UUID(as_uuid=True), ForeignKey("requirements.id"), nullable=False)
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("evidence.id"), nullable=False)
    retrieval_score = Column(Float, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    __table_args__ = (
        UniqueConstraint("requirement_id", "evidence_id"),
        Index("idx_req_evidence_requirement_id", "requirement_id"),
    )

class Response(Base):
    __tablename__ = "responses"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    query_id = Column(UUID(as_uuid=True), ForeignKey("regulatory_queries.id"), nullable=False)
    draft_text = Column(Text, nullable=True)
    sufficiency_status = Column(Text, nullable=True)
    gap_summary = Column(Text, nullable=True)
    status = Column(Text, nullable=False, server_default=text("'draft'"))
    version = Column(Integer, nullable=False, server_default=text("1"))
    reviewed_by = Column(Text, nullable=True)
    reviewed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    __table_args__ = (
        Index("idx_responses_query_id", "query_id"),
    )

class Claim(Base):
    __tablename__ = "claims"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    response_id = Column(UUID(as_uuid=True), ForeignKey("responses.id"), nullable=False)
    claim_code = Column(Text, nullable=False)
    claim_text = Column(Text, nullable=False)
    product_topic = Column(Text, nullable=False)
    validation_state = Column(Text, nullable=True)
    validation_reasoning = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    __table_args__ = (
        Index("idx_claims_response_id", "response_id"),
        Index("idx_claims_product_topic", "product_topic"),
    )

class Citation(Base):
    __tablename__ = "citations"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("evidence.id"), nullable=False)
    validated = Column(Boolean, nullable=False, server_default=text("FALSE"))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    __table_args__ = (
        Index("idx_citations_claim_id", "claim_id"),
    )

class Contradiction(Base):
    __tablename__ = "contradictions"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    claim_a_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    claim_b_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    classification = Column(Text, nullable=False)
    reasoning = Column(Text, nullable=False)
    resolved = Column(Boolean, nullable=False, server_default=text("FALSE"))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    __table_args__ = (
        Index("idx_contradictions_claim_a", "claim_a_id"),
        Index("idx_contradictions_claim_b", "claim_b_id"),
    )

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    event_type = Column(Text, nullable=False)
    response_id = Column(UUID(as_uuid=True), ForeignKey("responses.id"), nullable=True)
    actor = Column(Text, nullable=False)
    payload = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    __table_args__ = (
        Index("idx_audit_events_response_id", "response_id"),
    )

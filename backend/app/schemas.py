"""Pydantic request/response models - TASK-008."""
import uuid
from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    document_id: uuid.UUID
    version_id: uuid.UUID
    version_number: int
    status: str


class DocumentListItem(BaseModel):
    document_id: uuid.UUID
    filename: str
    doc_type: str
    jurisdiction: str | None
    current_version_number: int
    is_synthetic: bool
    created_at: str


class DocumentListResponse(BaseModel):
    documents: list[DocumentListItem]


class DocumentVersionItem(BaseModel):
    version_id: uuid.UUID
    version_number: int
    status: str
    uploaded_at: str


class DocumentDetailResponse(BaseModel):
    document_id: uuid.UUID
    filename: str
    doc_type: str
    versions: list[DocumentVersionItem]


# --- Query & Response schemas (TASK-014) ---

class QueryCreate(BaseModel):
    query_text: str


class RequirementResponseItem(BaseModel):
    req_code: str
    description: str
    status: str


class CitationResponseItem(BaseModel):
    evidence_id: uuid.UUID
    evidence_code: str
    document: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    section: str | None = None


class ClaimResponseItem(BaseModel):
    claim_id: uuid.UUID
    claim_code: str
    claim_text: str
    validation_state: str | None = None
    citations: list[CitationResponseItem]


class ContradictionResponseItem(BaseModel):
    contradiction_id: uuid.UUID
    claim_a: dict
    claim_b: dict
    classification: str
    reasoning: str


class QueryResponse(BaseModel):
    query_id: uuid.UUID
    response_id: uuid.UUID
    draft_text: str | None = None
    sufficiency_status: str | None = None
    gap_summary: str | None = None
    requirements: list[RequirementResponseItem]
    claims: list[ClaimResponseItem]
    contradictions: list[ContradictionResponseItem]
    status: str


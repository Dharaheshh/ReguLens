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

# --- Query schemas ---

class QueryRequest(BaseModel):
    query_text: str

class RequirementResponse(BaseModel):
    req_code: str
    description: str
    status: str | None = None

class EvidenceCitationResponse(BaseModel):
    evidence_id: uuid.UUID
    evidence_code: str
    document: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    section: str | None = None

class ClaimResponse(BaseModel):
    claim_id: uuid.UUID
    claim_code: str
    claim_text: str
    validation_state: str | None = None
    citations: list[EvidenceCitationResponse] = []

class ContradictionResponse(BaseModel):
    contradiction_id: uuid.UUID
    claim_a: dict
    claim_b: dict
    classification: str
    reasoning: str

class QueryResponse(BaseModel):
    query_id: uuid.UUID
    response_id: uuid.UUID | None = None
    draft_text: str | None = None
    sufficiency_status: str | None = None
    gap_summary: str | None = None
    requirements: list[RequirementResponse] = []
    claims: list[ClaimResponse] = []
    contradictions: list[ContradictionResponse] = []
    status: str | None = None


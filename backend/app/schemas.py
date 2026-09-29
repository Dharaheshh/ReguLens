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

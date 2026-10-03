"""Document endpoints - TASK-008.

POST /api/v1/documents
POST /api/v1/documents/{document_id}/versions
GET  /api/v1/documents
GET  /api/v1/documents/{document_id}
GET  /api/v1/documents/{document_id}/pdf   — Serve the raw PDF for human verification
GET  /api/v1/evidence/{evidence_code}      — Get chunk text + metadata for citation verification
"""
import os
import uuid
import shutil
import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db import SessionLocal
from app.models import Document, DocumentVersion, Chunk, Evidence
from app.schemas import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentListItem,
    DocumentDetailResponse,
    DocumentVersionItem,
)
from app.ingestion.pipeline import run_ingestion
from app.ingestion.parser import UnsupportedDocumentError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["documents"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
ALLOWED_DOC_TYPES = {"scientific_paper", "regulatory_guidance", "internal_study", "prior_response"}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/documents", status_code=201)
def create_document(
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    jurisdiction: Optional[str] = Form(None),
    is_synthetic: bool = Form(True),
    db: Session = Depends(get_db),
):
    """Upload a new document."""
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail={
            "error": {"code": "INVALID_FILE_TYPE", "message": "Only PDF files are accepted.", "details": {}}
        })

    if file.content_type and file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail={
            "error": {"code": "INVALID_FILE_TYPE", "message": "Only PDF files are accepted.", "details": {}}
        })

    if doc_type not in ALLOWED_DOC_TYPES:
        raise HTTPException(status_code=422, detail=f"Invalid doc_type. Must be one of: {ALLOWED_DOC_TYPES}")

    # Read file and check size
    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail={
            "error": {"code": "FILE_TOO_LARGE", "message": f"File exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit.", "details": {}}
        })

    # Create document row
    doc = Document(
        filename=file.filename,
        doc_type=doc_type,
        jurisdiction=jurisdiction,
        is_synthetic=is_synthetic,
    )
    db.add(doc)
    db.flush()

    # Create first version
    file_path = os.path.join(UPLOAD_DIR, f"{doc.id}_v1.pdf")
    with open(file_path, "wb") as f:
        f.write(content)

    version = DocumentVersion(
        document_id=doc.id,
        version_number=1,
        status="current",
        file_path=file_path,
    )
    db.add(version)
    db.flush()

    # Update current_version_id
    doc.current_version_id = version.id

    # Run ingestion pipeline
    try:
        run_ingestion(db, file_path, doc.id, version.id, doc_type)
        db.commit()
    except UnsupportedDocumentError as e:
        db.rollback()
        # Clean up saved file
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail={
            "error": {"code": "UNSUPPORTED_DOCUMENT", "message": str(e), "details": {}}
        })
    except Exception as e:
        db.rollback()
        if os.path.exists(file_path):
            os.remove(file_path)
        logger.exception("Ingestion failed")
        raise HTTPException(status_code=500, detail={
            "error": {"code": "INGESTION_FAILED", "message": f"Ingestion failed: {e}", "details": {}}
        })

    return DocumentUploadResponse(
        document_id=doc.id,
        version_id=version.id,
        version_number=1,
        status="processing",
    )


@router.post("/documents/{document_id}/versions", status_code=201)
def create_version(
    document_id: uuid.UUID,
    file: UploadFile = File(...),
    is_synthetic: bool = Form(True),
    db: Session = Depends(get_db),
):
    """Upload a new version of an existing document."""
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail={
            "error": {"code": "INVALID_FILE_TYPE", "message": "Only PDF files are accepted.", "details": {}}
        })

    # Find existing document
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail={
            "error": {"code": "NOT_FOUND", "message": "Document not found.", "details": {}}
        })

    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail={
            "error": {"code": "FILE_TOO_LARGE", "message": "File too large.", "details": {}}
        })

    # Determine next version number
    current_max = db.query(DocumentVersion).filter(
        DocumentVersion.document_id == document_id
    ).count()
    new_version_number = current_max + 1

    # Mark previous versions as superseded
    db.query(DocumentVersion).filter(
        DocumentVersion.document_id == document_id,
        DocumentVersion.status == "current",
    ).update({"status": "superseded"})

    file_path = os.path.join(UPLOAD_DIR, f"{document_id}_v{new_version_number}.pdf")
    with open(file_path, "wb") as f:
        f.write(content)

    version = DocumentVersion(
        document_id=document_id,
        version_number=new_version_number,
        status="current",
        file_path=file_path,
    )
    db.add(version)
    db.flush()

    doc.current_version_id = version.id

    try:
        run_ingestion(db, file_path, doc.id, version.id, doc.doc_type)
        db.commit()
    except UnsupportedDocumentError as e:
        db.rollback()
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail={
            "error": {"code": "UNSUPPORTED_DOCUMENT", "message": str(e), "details": {}}
        })
    except Exception as e:
        db.rollback()
        if os.path.exists(file_path):
            os.remove(file_path)
        logger.exception("Ingestion failed")
        raise HTTPException(status_code=500, detail={
            "error": {"code": "INGESTION_FAILED", "message": f"Ingestion failed: {e}", "details": {}}
        })

    return DocumentUploadResponse(
        document_id=doc.id,
        version_id=version.id,
        version_number=new_version_number,
        status="processing",
    )


@router.get("/documents")
def list_documents(
    doc_type: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all documents."""
    query = db.query(Document)
    if doc_type:
        query = query.filter(Document.doc_type == doc_type)
    if jurisdiction:
        query = query.filter(Document.jurisdiction == jurisdiction)

    docs = query.all()
    items = []
    for doc in docs:
        current_version = db.query(DocumentVersion).filter(
            DocumentVersion.id == doc.current_version_id
        ).first()
        items.append(DocumentListItem(
            document_id=doc.id,
            filename=doc.filename,
            doc_type=doc.doc_type,
            jurisdiction=doc.jurisdiction,
            current_version_number=current_version.version_number if current_version else 1,
            is_synthetic=doc.is_synthetic,
            created_at=doc.created_at.isoformat() if doc.created_at else "",
        ))

    return DocumentListResponse(documents=items)


@router.get("/documents/{document_id}")
def get_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Get a document with its version history."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail={
            "error": {"code": "NOT_FOUND", "message": "Document not found.", "details": {}}
        })

    versions = db.query(DocumentVersion).filter(
        DocumentVersion.document_id == document_id
    ).order_by(DocumentVersion.version_number).all()

    version_items = [
        DocumentVersionItem(
            version_id=v.id,
            version_number=v.version_number,
            status=v.status,
            uploaded_at=v.uploaded_at.isoformat() if v.uploaded_at else "",
        )
        for v in versions
    ]

    return DocumentDetailResponse(
        document_id=doc.id,
        filename=doc.filename,
        doc_type=doc.doc_type,
        versions=version_items,
    )


@router.get("/documents/{document_id}/pdf")
def serve_document_pdf(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Serve the current PDF file for a document so the user can verify citations manually.

    Returns the raw PDF binary with the correct Content-Disposition header so the
    browser renders it inline (or downloads it).  This allows any human reviewer to
    open the source document and cross-check the quoted evidence text against the
    original page.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail={
            "error": {"code": "NOT_FOUND", "message": "Document not found.", "details": {}}
        })

    # Resolve the current version's file path
    version = db.query(DocumentVersion).filter(
        DocumentVersion.id == doc.current_version_id
    ).first()
    if not version or not os.path.exists(version.file_path):
        raise HTTPException(status_code=404, detail={
            "error": {"code": "FILE_NOT_FOUND", "message": "PDF file not found on disk.", "details": {}}
        })

    return FileResponse(
        path=version.file_path,
        media_type="application/pdf",
        filename=doc.filename,
        # inline so the browser opens it in its PDF viewer, not a download
        headers={"Content-Disposition": f'inline; filename="{doc.filename}"'},
    )


@router.get("/evidence/{evidence_code}")
def get_evidence_detail(
    evidence_code: str,
    db: Session = Depends(get_db),
):
    """Return the full chunk text, page range, section, and document metadata for
    a given evidence code.

    This is the citation verification endpoint — the frontend calls it when the
    user clicks a citation chip so they can read the exact extracted text and
    then open the source PDF to manually cross-check it.
    """
    # Join Evidence → Chunk → DocumentVersion → Document in one query
    evidence = db.query(Evidence).filter(Evidence.evidence_code == evidence_code).first()
    if not evidence:
        raise HTTPException(status_code=404, detail={
            "error": {"code": "NOT_FOUND", "message": f"Evidence '{evidence_code}' not found.", "details": {}}
        })

    chunk = db.query(Chunk).filter(Chunk.id == evidence.chunk_id).first()
    doc = db.query(Document).filter(Document.id == evidence.document_id).first()

    return {
        "evidence_code": evidence.evidence_code,
        "evidence_id": str(evidence.id),
        "chunk_text": chunk.content if chunk else None,
        "page_start": chunk.page_start if chunk else None,
        "page_end": chunk.page_end if chunk else None,
        "section": chunk.section if chunk else None,
        "document_id": str(evidence.document_id),
        "document_filename": doc.filename if doc else None,
        "doc_type": doc.doc_type if doc else None,
        # Convenience URL so the frontend can link directly to the PDF viewer
        "pdf_url": f"/api/v1/documents/{evidence.document_id}/pdf",
    }

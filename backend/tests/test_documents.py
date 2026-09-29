"""Tests for TASK-008 - Document API endpoints + ingestion integration."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
SAMPLE_PDF = os.path.join(FIXTURE_DIR, "sample_3page.pdf")


def test_upload_document():
    """POST /api/v1/documents creates a document and returns 201."""
    with open(SAMPLE_PDF, "rb") as f:
        response = client.post(
            "/api/v1/documents",
            files={"file": ("sample_3page.pdf", f, "application/pdf")},
            data={"doc_type": "scientific_paper", "is_synthetic": "true"},
        )
    assert response.status_code == 201, response.text
    data = response.json()
    assert "document_id" in data
    assert "version_id" in data
    assert data["version_number"] == 1
    assert data["status"] == "processing"


def test_upload_non_pdf_rejected():
    """POST /api/v1/documents with non-PDF returns 400."""
    response = client.post(
        "/api/v1/documents",
        files={"file": ("test.txt", b"not a pdf", "text/plain")},
        data={"doc_type": "scientific_paper"},
    )
    assert response.status_code == 400


def test_list_documents():
    """GET /api/v1/documents returns a documents list."""
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert isinstance(data["documents"], list)


def test_get_document_detail():
    """Upload a doc then GET /api/v1/documents/{id} returns detail with versions."""
    # First upload
    with open(SAMPLE_PDF, "rb") as f:
        upload_resp = client.post(
            "/api/v1/documents",
            files={"file": ("sample_3page.pdf", f, "application/pdf")},
            data={"doc_type": "internal_study", "is_synthetic": "true"},
        )
    assert upload_resp.status_code == 201
    doc_id = upload_resp.json()["document_id"]

    # Get detail
    detail_resp = client.get(f"/api/v1/documents/{doc_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["document_id"] == doc_id
    assert detail["filename"] == "sample_3page.pdf"
    assert len(detail["versions"]) >= 1
    assert detail["versions"][0]["version_number"] == 1
    assert detail["versions"][0]["status"] == "current"


def test_upload_new_version():
    """POST /api/v1/documents/{id}/versions creates a new version."""
    # First upload
    with open(SAMPLE_PDF, "rb") as f:
        upload_resp = client.post(
            "/api/v1/documents",
            files={"file": ("sample_3page.pdf", f, "application/pdf")},
            data={"doc_type": "regulatory_guidance", "is_synthetic": "true"},
        )
    assert upload_resp.status_code == 201
    doc_id = upload_resp.json()["document_id"]

    # Upload version 2
    with open(SAMPLE_PDF, "rb") as f:
        v2_resp = client.post(
            f"/api/v1/documents/{doc_id}/versions",
            files={"file": ("sample_3page_v2.pdf", f, "application/pdf")},
            data={"is_synthetic": "true"},
        )
    assert v2_resp.status_code == 201
    v2_data = v2_resp.json()
    assert v2_data["version_number"] == 2

    # Check detail - old version should be superseded
    detail_resp = client.get(f"/api/v1/documents/{doc_id}")
    detail = detail_resp.json()
    assert len(detail["versions"]) == 2
    statuses = {v["version_number"]: v["status"] for v in detail["versions"]}
    assert statuses[1] == "superseded"
    assert statuses[2] == "current"


def test_get_nonexistent_document():
    """GET /api/v1/documents/{nonexistent_id} returns 404."""
    import uuid
    response = client.get(f"/api/v1/documents/{uuid.uuid4()}")
    assert response.status_code == 404

def test_concurrent_uploads_unique_evidence_codes():
    """Simulates two concurrent ingestion calls to confirm evidence_codes are unique."""
    import concurrent.futures
    from app.db import SessionLocal
    from app.models import Evidence

    def upload_doc():
        with open(SAMPLE_PDF, "rb") as f:
            resp = client.post(
                "/api/v1/documents",
                files={"file": ("sample_3page.pdf", f, "application/pdf")},
                data={"doc_type": "scientific_paper", "is_synthetic": "true"},
            )
        return resp.json()

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(upload_doc)
        future2 = executor.submit(upload_doc)
        doc1 = future1.result()
        doc2 = future2.result()

    assert "document_id" in doc1
    assert "document_id" in doc2

    db = SessionLocal()
    try:
        evd1 = db.query(Evidence).filter(Evidence.document_id == doc1["document_id"]).all()
        evd2 = db.query(Evidence).filter(Evidence.document_id == doc2["document_id"]).all()
        
        codes1 = {e.evidence_code for e in evd1}
        codes2 = {e.evidence_code for e in evd2}
        
        # Check they both generated evidence codes
        assert len(codes1) > 0
        assert len(codes2) > 0
        
        # Check there is no intersection between the generated codes
        assert len(codes1.intersection(codes2)) == 0
    finally:
        db.close()

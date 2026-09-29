import os
import sys
import uuid
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db import SessionLocal
from app.models import RegulatoryQuery, Requirement, Response, Claim, Citation
from app.generation.requirement_extraction import RequirementExtractionOutput, RequirementSchema
from app.generation.response_generation import ResponseGenerationOutput, ClaimProposal

client = TestClient(app)

@patch("app.generation.requirement_extraction.call_with_retry_and_fallback")
@patch("app.retrieval.hybrid_search.hybrid_search")
@patch("app.generation.response_generation.call_with_retry_and_fallback")
def test_post_query_success(mock_response_llm, mock_hybrid_search, mock_req_llm):
    # Mock Requirement LLM
    mock_req_llm.return_value = RequirementExtractionOutput(
        requirements=[
            RequirementSchema(
                req_code="REQ-01",
                description="Test requirement",
                keywords=["test"]
            )
        ]
    )
    
    # Mock Hybrid Search
    unique_evd = f"EVD-{uuid.uuid4().hex[:5]}"
    class MockSearchResult:
        chunk_id = uuid.uuid4()
        evidence_id = uuid.uuid4()
        evidence_code = unique_evd
        content = "Test content"
        score = 0.99
        source_type = "scientific_paper"
    
    mock_hybrid_search.return_value = [MockSearchResult()]
    
    # Mock Response LLM
    mock_response_llm.return_value = ResponseGenerationOutput(
        draft_text="Test draft",
        claims=[
            ClaimProposal(
                claim_code="CLM-001",
                claim_text="Test claim",
                product_topic="test",
                req_code="REQ-01",
                cited_evidence_codes=[unique_evd]
            )
        ]
    )
    
    # We need an evidence row with the unique EVD in the database so the citation validator works
    db = SessionLocal()
    try:
        from app.models import Evidence, Chunk, Document, DocumentVersion
        doc = Document(filename="test", doc_type="test")
        db.add(doc)
        db.flush()
        ver = DocumentVersion(document_id=doc.id, version_number=1, file_path="test")
        db.add(ver)
        db.flush()
        chunk = Chunk(document_version_id=ver.id, content="test")
        db.add(chunk)
        db.flush()
        evd = Evidence(
            id=MockSearchResult.evidence_id,
            evidence_code=unique_evd,
            chunk_id=chunk.id,
            document_id=doc.id,
            document_version_id=ver.id,
            source_type="scientific_paper"
        )
        db.add(evd)
        db.commit()
    finally:
        db.close()

    res = client.post("/api/v1/queries", json={"query_text": "Is this a test?"})
    
    assert res.status_code == 200
    data = res.json()
    assert data["query_id"] is not None
    assert data["response_id"] is not None
    assert data["draft_text"] == "Test draft"
    assert data["status"] == "draft"
    
    assert len(data["requirements"]) == 1
    assert data["requirements"][0]["req_code"] == "REQ-01"
    
    assert len(data["claims"]) == 1
    assert data["claims"][0]["claim_code"] == "CLM-001"
    
    # Citations should be resolved
    assert len(data["claims"][0]["citations"]) == 1
    assert data["claims"][0]["citations"][0]["evidence_code"] == unique_evd
    
    # Validation state shouldn't be UNSUPPORTED because the citation was found
    assert data["claims"][0]["validation_state"] is None

@patch("app.generation.requirement_extraction.call_with_retry_and_fallback")
def test_post_query_llm_failure(mock_req_llm):
    from app.llm.provider import LLMCallError
    mock_req_llm.side_effect = LLMCallError("Test LLM Failure")
    
    # For requirement extraction, LLMCallError actually falls back locally.
    # So to trigger a total failure, we'll patch generate_response's LLM instead.
    pass

@patch("app.generation.response_generation.call_with_retry_and_fallback")
def test_post_query_response_llm_failure(mock_response_llm):
    from app.llm.provider import LLMCallError
    mock_response_llm.side_effect = LLMCallError("Test Generation Failure")
    
    res = client.post("/api/v1/queries", json={"query_text": "Is this a test?"})
    assert res.status_code == 500
    assert res.json()["detail"]["code"] == "LLM_FAILED"

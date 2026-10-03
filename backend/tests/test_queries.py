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
@patch("app.routers.queries.hybrid_search")
@patch("app.generation.response_generation.call_with_retry_and_fallback")
@patch("app.validation.claim_validator.call_with_retry_and_fallback")
def test_post_query_success(mock_validator_llm, mock_response_llm, mock_hybrid_search, mock_req_llm):
    # Mock Claim Validator LLM
    from app.validation.claim_validator import SemanticValidationOutput
    mock_validator_llm.return_value = SemanticValidationOutput(
        validation_state="SUPPORTED",
        reasoning="Test reasoning",
        supported_portion="Test"
    )
    
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
    assert data["claims"][0]["validation_state"] == "SUPPORTED"

@patch("app.generation.requirement_extraction.call_with_retry_and_fallback")
def test_post_query_llm_failure(mock_req_llm):
    from app.llm.provider import LLMCallError
    mock_req_llm.side_effect = LLMCallError("Test LLM Failure")
    pass

@patch("app.generation.requirement_extraction.call_with_retry_and_fallback")
@patch("app.routers.queries.hybrid_search")
@patch("app.generation.response_generation.call_with_retry_and_fallback")
def test_post_query_response_llm_failure(mock_response_llm, mock_hybrid_search, mock_req_llm):
    mock_req_llm.return_value = RequirementExtractionOutput(
        requirements=[RequirementSchema(req_code="REQ-01", description="desc", keywords=[])]
    )
    
    unique_evd = f"EVD-{uuid.uuid4().hex[:5]}"
    class MockSearchResult:
        chunk_id = uuid.uuid4()
        evidence_id = uuid.uuid4()
        evidence_code = unique_evd
        content = "Test content"
        score = 0.99
        source_type = "scientific_paper"
    
    # MUST return evidence to pass the evidence gate
    mock_hybrid_search.return_value = [MockSearchResult()]

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

    from app.llm.provider import LLMCallError
    mock_response_llm.side_effect = LLMCallError("Test Generation Failure")
    
    res = client.post("/api/v1/queries", json={"query_text": "Is this a test?"})
    assert res.status_code == 500
    assert res.json()["detail"]["code"] == "LLM_FAILED"


# --- Phase 2: Evidence Gate Tests ---

@patch("app.generation.requirement_extraction.call_with_retry_and_fallback")
@patch("app.routers.queries.hybrid_search")
@patch("app.generation.response_generation.generate_response")
def test_post_query_no_evidence_short_circuit(mock_generate, mock_hybrid, mock_req_llm):
    """If ALL requirements return zero evidence, generation is NEVER called."""
    mock_req_llm.return_value = RequirementExtractionOutput(
        requirements=[RequirementSchema(req_code="REQ-01", description="irrelevant", keywords=["hi"])]
    )
    # Return empty list from hybrid search simulating a relevance floor failure
    mock_hybrid.return_value = []
    
    res = client.post("/api/v1/queries", json={"query_text": "hi"})
    assert res.status_code == 200
    
    data = res.json()
    assert data["sufficiency_status"] == "INSUFFICIENT"
    assert "No relevant evidence was found" in data["gap_summary"]
    assert data["draft_text"] is None
    assert data["claims"] == []
    
    # CRITICAL: generation must not have been called
    assert mock_generate.call_count == 0


@patch("app.generation.requirement_extraction.call_with_retry_and_fallback")
@patch("app.routers.queries.hybrid_search")
@patch("app.generation.response_generation.call_with_retry_and_fallback")
def test_post_query_partial_evidence_calls_generation(mock_response_llm, mock_hybrid, mock_req_llm):
    """If AT LEAST ONE requirement has evidence, generation is called."""
    mock_req_llm.return_value = RequirementExtractionOutput(
        requirements=[
            RequirementSchema(req_code="REQ-01", description="has evidence", keywords=["yes"]),
            RequirementSchema(req_code="REQ-02", description="no evidence", keywords=["no"])
        ]
    )
    
    unique_evd = f"EVD-{uuid.uuid4().hex[:5]}"
    class MockSearchResult:
        chunk_id = uuid.uuid4()
        evidence_id = uuid.uuid4()
        evidence_code = unique_evd
        content = "Test content"
        score = 0.99
        source_type = "scientific_paper"

    # Return evidence for the first call, empty for the second call
    mock_hybrid.side_effect = [
        [MockSearchResult()],
        []
    ]

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
    
    mock_response_llm.return_value = ResponseGenerationOutput(
        draft_text="Test draft partial",
        claims=[]
    )
    
    res = client.post("/api/v1/queries", json={"query_text": "partial query"})
    assert res.status_code == 200
    
    # Generation was called because side_effect was used up (meaning it hit both requirements and proceeded)
    assert mock_response_llm.call_count == 1
    data = res.json()
    assert data["draft_text"] == "Test draft partial"

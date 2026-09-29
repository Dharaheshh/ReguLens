"""Tests for Query orchestration - TASK-014."""
import os
import sys
import uuid
import json
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db import SessionLocal
from app.models import RegulatoryQuery, Response, Requirement, Claim, Citation
from app.generation.requirement_extraction import RequirementExtractionOutput, RequirementSchema
from app.generation.response_generation import ResponseGenerationOutput, ClaimProposal
from app.llm.provider import LLMCallError

client = TestClient(app)

@pytest.fixture
def mock_pipeline():
    """Mock LLM calls to prevent real network requests during integration test."""
    # Mock requirement extraction output
    req_out = RequirementExtractionOutput(
        requirements=[
            RequirementSchema(
                req_code="REQ-01",
                description="Test req",
                keywords=["test"]
            )
        ]
    )
    
    # Mock response generation output
    res_out = ResponseGenerationOutput(
        draft_text="Test draft",
        claims=[
            ClaimProposal(
                claim_code="CLM-01",
                claim_text="Test claim",
                product_topic="Topic",
                req_code="REQ-01",
                cited_evidence_codes=["EVD-TEST"]
            )
        ]
    )
    
    with patch("app.generation.requirement_extraction.call_with_retry_and_fallback", return_value=req_out) as m_req:
        with patch("app.generation.response_generation.call_with_retry_and_fallback", return_value=res_out) as m_res:
            yield m_req, m_res


def test_empty_query():
    """Empty query fails immediately without touching the DB."""
    resp = client.post("/api/v1/queries", json={"query_text": ""})
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"].lower()


def test_query_pipeline_success(mock_pipeline):
    """Test standard successful query pipeline execution."""
    resp = client.post("/api/v1/queries", json={"query_text": "Is it safe?"})
    assert resp.status_code == 200
    
    data = resp.json()
    assert data["query_id"]
    assert data["response_id"]
    assert data["draft_text"] == "Test draft"
    assert data["status"] == "draft"
    
    # Requirements
    assert len(data["requirements"]) == 1
    assert data["requirements"][0]["req_code"] == "REQ-01"
    
    # Claims
    assert len(data["claims"]) == 1
    assert data["claims"][0]["claim_code"] == "CLM-01"
    
    # Contradictions are empty for now
    assert data["contradictions"] == []
    
    # Verify persistence
    db = SessionLocal()
    try:
        q = db.query(RegulatoryQuery).filter_by(id=data["query_id"]).first()
        assert q is not None
        assert q.query_text == "Is it safe?"
        
        r = db.query(Response).filter_by(id=data["response_id"]).first()
        assert r is not None
        assert r.draft_text == "Test draft"
    finally:
        db.close()


def test_llm_failure_response_persisted():
    """If response generation LLM fails entirely, we get a 500 but a response row is saved with status LLM_FAILED."""
    req_out = RequirementExtractionOutput(
        requirements=[RequirementSchema(req_code="REQ-01", description="Test", keywords=[])]
    )
    
    with patch("app.generation.requirement_extraction.call_with_retry_and_fallback", return_value=req_out):
        with patch("app.generation.response_generation.call_with_retry_and_fallback", side_effect=LLMCallError("Failed")):
            resp = client.post("/api/v1/queries", json={"query_text": "Fail test"})
            
            assert resp.status_code == 500
            assert resp.json()["detail"] == "LLM_FAILED"
            
            # Verify the response was persisted with LLM_FAILED
            db = SessionLocal()
            try:
                q = db.query(RegulatoryQuery).filter_by(query_text="Fail test").first()
                resps = db.query(Response).filter_by(query_id=q.id).all()
                assert len(resps) == 1
                assert resps[0].status == "LLM_FAILED"
            finally:
                db.close()

def test_get_query_success(mock_pipeline):
    """Test retrieving an existing query."""
    create_resp = client.post("/api/v1/queries", json={"query_text": "Is it safe for GET?"})
    query_id = create_resp.json()["query_id"]
    
    get_resp = client.get(f"/api/v1/queries/{query_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["query_id"] == query_id
    assert get_resp.json()["draft_text"] == "Test draft"

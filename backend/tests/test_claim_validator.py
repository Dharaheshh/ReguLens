"""Tests for Claim/Evidence Validation (TASK-015)."""
import os
import sys
import uuid
import pytest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import SessionLocal
from app.models import Claim, Citation, Evidence, Chunk, RegulatoryQuery, Response, Document, DocumentVersion
from app.validation.claim_validator import validate_claim, ClaimValidationOutput
from app.llm.provider import LLMCallError

@pytest.fixture
def setup_db_for_claim():
    db = SessionLocal()
    # Create necessary hierarchy
    doc = Document(filename="test.pdf", doc_type="scientific_paper", is_synthetic=True)
    db.add(doc)
    db.flush()
    
    dv = DocumentVersion(document_id=doc.id, version_number=1, status="current", file_path="test.pdf")
    db.add(dv)
    db.flush()
    
    chunk = Chunk(document_version_id=dv.id, content="Signal detected in 1 of 100 samples, below reporting threshold.", embedding=[0.1]*384)
    db.add(chunk)
    db.flush()
    
    unique_id = str(uuid.uuid4())[:8]
    ev = Evidence(evidence_code=f"EVD-{unique_id}", chunk_id=chunk.id, document_id=doc.id, document_version_id=dv.id, source_type="test")
    db.add(ev)
    db.flush()
    
    q = RegulatoryQuery(query_text="Test query")
    db.add(q)
    db.flush()
    
    r = Response(query_id=q.id, status="draft")
    db.add(r)
    db.flush()
    
    claim = Claim(response_id=r.id, claim_code="CLM-TEST", claim_text="No contamination detected.", product_topic="topic")
    db.add(claim)
    db.flush()
    
    yield db, claim, ev
    db.rollback()
    db.close()


def test_zero_citations_unsupported(setup_db_for_claim):
    db, claim, _ = setup_db_for_claim
    # No citations created for this claim
    validate_claim(db, claim.id)
    assert claim.validation_state == "UNSUPPORTED"
    assert "No validated citations" in claim.validation_reasoning


def test_overclaim(setup_db_for_claim):
    db, claim, ev = setup_db_for_claim
    cit = Citation(claim_id=claim.id, evidence_id=ev.id, validated=True)
    db.add(cit)
    db.commit()
    
    mock_out = ClaimValidationOutput(
        validation_state="OVERCLAIM",
        reasoning="The evidence says signal was detected below threshold, but claim says no contamination.",
        supported_portion="Contamination was not detected above the assay reporting threshold."
    )
    
    with patch("app.validation.claim_validator.call_with_retry_and_fallback", return_value=mock_out):
        validate_claim(db, claim.id)
        
    assert claim.validation_state == "OVERCLAIM"
    assert "Supported portion: Contamination was not detected" in claim.validation_reasoning


def test_validation_failed(setup_db_for_claim):
    db, claim, ev = setup_db_for_claim
    cit = Citation(claim_id=claim.id, evidence_id=ev.id, validated=True)
    db.add(cit)
    db.commit()
    
    with patch("app.validation.claim_validator.call_with_retry_and_fallback", side_effect=LLMCallError("Crash")):
        validate_claim(db, claim.id)
        
    assert claim.validation_state == "VALIDATION_FAILED"

import os
import sys
import uuid
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app.db import SessionLocal
from app.models import Claim, Citation, Evidence, Chunk, Document, DocumentVersion
from app.validation.claim_validator import validate_claim_semantics, SemanticValidationOutput

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def setup_claim_with_evidence(db, claim_state=None, has_citations=True):
    # Setup document, version, chunk, evidence
    doc = Document(filename="test.pdf", doc_type="test")
    db.add(doc)
    db.flush()
    ver = DocumentVersion(document_id=doc.id, version_number=1, file_path="test")
    db.add(ver)
    db.flush()
    chunk = Chunk(document_version_id=ver.id, content="This is test evidence.")
    db.add(chunk)
    db.flush()
    evd = Evidence(evidence_code=f"EVD-{uuid.uuid4().hex[:5]}", chunk_id=chunk.id, document_id=doc.id, document_version_id=ver.id, source_type="test")
    db.add(evd)
    db.flush()
    
    # Setup response and claim
    from app.models import Response, RegulatoryQuery
    q = RegulatoryQuery(query_text="Test query")
    db.add(q)
    db.flush()
    r = Response(query_id=q.id)
    db.add(r)
    db.flush()
    claim = Claim(response_id=r.id, claim_code="CLM-01", claim_text="This is a test claim.", product_topic="test", validation_state=claim_state)
    db.add(claim)
    db.flush()
    
    if has_citations:
        cit = Citation(claim_id=claim.id, evidence_id=evd.id, validated=True)
        db.add(cit)
        db.flush()
        
    return claim.id

@patch("app.validation.claim_validator.call_with_retry_and_fallback")
def test_validate_claim_supported(mock_llm, db_session):
    mock_llm.return_value = SemanticValidationOutput(
        validation_state="SUPPORTED",
        reasoning="Matches perfectly."
    )
    
    claim_id = setup_claim_with_evidence(db_session)
    res = validate_claim_semantics(db_session, claim_id)
    
    assert res is not None
    assert res.validation_state == "SUPPORTED"
    
    # Verify DB updated
    claim = db_session.query(Claim).filter(Claim.id == claim_id).first()
    assert claim.validation_state == "SUPPORTED"
    assert claim.validation_reasoning == "Matches perfectly."

@patch("app.validation.claim_validator.call_with_retry_and_fallback")
def test_validate_claim_missing_citations(mock_llm, db_session):
    # Deterministic check should mark it UNSUPPORTED without calling LLM
    claim_id = setup_claim_with_evidence(db_session, has_citations=False)
    res = validate_claim_semantics(db_session, claim_id)
    
    assert res is not None
    assert res.validation_state == "UNSUPPORTED"
    mock_llm.assert_not_called()
    
    claim = db_session.query(Claim).filter(Claim.id == claim_id).first()
    assert claim.validation_state == "UNSUPPORTED"

def test_validate_claim_already_unsupported(db_session):
    claim_id = setup_claim_with_evidence(db_session, claim_state="UNSUPPORTED")
    res = validate_claim_semantics(db_session, claim_id)
    
    assert res is None  # Skips semantic validation entirely

@patch("app.validation.claim_validator.call_with_retry_and_fallback")
def test_validate_claim_overclaim(mock_llm, db_session):
    mock_llm.return_value = SemanticValidationOutput(
        validation_state="OVERCLAIM",
        reasoning="States things beyond evidence."
    )
    
    claim_id = setup_claim_with_evidence(db_session)
    res = validate_claim_semantics(db_session, claim_id)
    
    assert res.validation_state == "OVERCLAIM"
    claim = db_session.query(Claim).filter(Claim.id == claim_id).first()
    assert claim.validation_state == "OVERCLAIM"

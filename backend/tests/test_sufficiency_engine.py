import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app.db import SessionLocal
from app.models import RegulatoryQuery, Requirement, RequirementEvidence, Evidence, Chunk, Document, DocumentVersion, Response
from app.validation.sufficiency_engine import run_sufficiency_check, THRESHOLD_HIGH, THRESHOLD_LOW

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def setup_query_and_requirement(db, score=None, count=1):
    q = RegulatoryQuery(query_text="Test query")
    db.add(q)
    db.flush()
    r = Response(query_id=q.id)
    db.add(r)
    req = Requirement(query_id=q.id, req_code="REQ-01", description="Test req", keywords=[])
    db.add(req)
    db.flush()
    
    if score is not None:
        doc = Document(filename="test", doc_type="test")
        db.add(doc)
        db.flush()
        ver = DocumentVersion(document_id=doc.id, version_number=1, file_path="test")
        db.add(ver)
        db.flush()
        
        for i in range(count):
            chunk = Chunk(document_version_id=ver.id, content=f"Test {i}")
            db.add(chunk)
            db.flush()
            evd = Evidence(evidence_code=f"EVD-{uuid.uuid4().hex[:5]}", chunk_id=chunk.id, document_id=doc.id, document_version_id=ver.id, source_type="test")
            db.add(evd)
            db.flush()
            
            re = RequirementEvidence(requirement_id=req.id, evidence_id=evd.id, retrieval_score=score)
            db.add(re)
        db.flush()
        
    return q.id

def test_sufficiency_covered(db_session):
    q_id = setup_query_and_requirement(db_session, score=THRESHOLD_HIGH + 0.01, count=2)
    run_sufficiency_check(db_session, q_id)
    
    req = db_session.query(Requirement).filter(Requirement.query_id == q_id).first()
    assert req.status == "COVERED"
    
    res = db_session.query(Response).filter(Response.query_id == q_id).first()
    assert res.sufficiency_status == "SUFFICIENT"
    assert res.gap_summary is None

def test_sufficiency_partially_covered_score(db_session):
    # High score but only 1 match -> partially covered
    q_id = setup_query_and_requirement(db_session, score=THRESHOLD_HIGH + 0.01, count=1)
    run_sufficiency_check(db_session, q_id)
    
    req = db_session.query(Requirement).filter(Requirement.query_id == q_id).first()
    assert req.status == "PARTIALLY_COVERED"
    
    res = db_session.query(Response).filter(Response.query_id == q_id).first()
    assert res.sufficiency_status == "PARTIALLY_SUFFICIENT"
    assert "partially covered" in res.gap_summary

def test_sufficiency_not_covered(db_session):
    q_id = setup_query_and_requirement(db_session, score=THRESHOLD_LOW - 0.001, count=1)
    run_sufficiency_check(db_session, q_id)
    
    req = db_session.query(Requirement).filter(Requirement.query_id == q_id).first()
    assert req.status == "NOT_COVERED"
    
    res = db_session.query(Response).filter(Response.query_id == q_id).first()
    assert res.sufficiency_status == "INSUFFICIENT"
    assert "not covered" in res.gap_summary

def test_sufficiency_no_evidence(db_session):
    q_id = setup_query_and_requirement(db_session, score=None)
    run_sufficiency_check(db_session, q_id)
    
    req = db_session.query(Requirement).filter(Requirement.query_id == q_id).first()
    assert req.status == "NOT_COVERED"
    
    res = db_session.query(Response).filter(Response.query_id == q_id).first()
    assert res.sufficiency_status == "INSUFFICIENT"

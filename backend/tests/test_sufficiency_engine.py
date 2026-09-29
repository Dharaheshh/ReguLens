"""Tests for Evidence Sufficiency (TASK-016)."""
import os
import sys
import uuid
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import SessionLocal
from app.models import RegulatoryQuery, Response, Requirement, RequirementEvidence, Evidence, Chunk, Document, DocumentVersion
from app.validation.sufficiency_engine import evaluate_sufficiency

@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()

def setup_base(db, req_count=1):
    q = RegulatoryQuery(query_text="Test query")
    db.add(q)
    db.flush()
    
    r = Response(query_id=q.id, status="draft")
    db.add(r)
    db.flush()
    
    reqs = []
    for i in range(req_count):
        req = Requirement(query_id=q.id, req_code=f"REQ-{i+1}", description="test", keywords=["test"])
        db.add(req)
        db.flush()
        reqs.append(req)
        
    doc = Document(filename="test.pdf", doc_type="scientific_paper", is_synthetic=True)
    db.add(doc)
    db.flush()
    
    dv = DocumentVersion(document_id=doc.id, version_number=1, status="current", file_path="test.pdf")
    db.add(dv)
    db.flush()
        
    return q, r, reqs, doc, dv

def add_evidence(db, doc, dv, score, req_id):
    chunk = Chunk(document_version_id=dv.id, content="test", embedding=[0.1]*384)
    db.add(chunk)
    db.flush()
    
    unique_id = str(uuid.uuid4())[:8]
    ev = Evidence(evidence_code=f"EVD-{unique_id}", chunk_id=chunk.id, document_id=doc.id, document_version_id=dv.id, source_type="test")
    db.add(ev)
    db.flush()
    
    re = RequirementEvidence(requirement_id=req_id, evidence_id=ev.id, retrieval_score=score)
    db.add(re)
    db.flush()
    return re


def test_sufficient_all_covered(db):
    q, r, reqs, doc, dv = setup_base(db, req_count=2)
    # Req 1: score 0.02, 2 matches -> COVERED
    add_evidence(db, doc, dv, 0.02, reqs[0].id)
    add_evidence(db, doc, dv, 0.02, reqs[0].id)
    # Req 2: score 0.02, 2 matches -> COVERED
    add_evidence(db, doc, dv, 0.02, reqs[1].id)
    add_evidence(db, doc, dv, 0.02, reqs[1].id)
    db.commit()
    
    status, gap = evaluate_sufficiency(db, r.id)
    assert status == "SUFFICIENT"
    assert reqs[0].status == "COVERED"
    assert reqs[1].status == "COVERED"


def test_insufficient_one_missing(db):
    q, r, reqs, doc, dv = setup_base(db, req_count=2)
    # Req 1: score 0.02, 2 matches -> COVERED
    add_evidence(db, doc, dv, 0.02, reqs[0].id)
    add_evidence(db, doc, dv, 0.02, reqs[0].id)
    # Req 2: no evidence -> NOT_COVERED
    db.commit()
    
    status, gap = evaluate_sufficiency(db, r.id)
    assert status == "INSUFFICIENT"
    assert reqs[0].status == "COVERED"
    assert reqs[1].status == "NOT_COVERED"
    assert "REQ-2 is not covered" in gap


def test_partially_sufficient(db):
    q, r, reqs, doc, dv = setup_base(db, req_count=2)
    # Req 1: score 0.02, 2 matches -> COVERED
    add_evidence(db, doc, dv, 0.02, reqs[0].id)
    add_evidence(db, doc, dv, 0.02, reqs[0].id)
    # Req 2: score 0.012, 1 match -> PARTIALLY_COVERED (>= LOW, not HIGH+2)
    add_evidence(db, doc, dv, 0.012, reqs[1].id)
    db.commit()
    
    status, gap = evaluate_sufficiency(db, r.id)
    assert status == "PARTIALLY_SUFFICIENT"
    assert reqs[0].status == "COVERED"
    assert reqs[1].status == "PARTIALLY_COVERED"
    assert "REQ-2 is only partially covered" in gap


def test_zero_evidence(db):
    q, r, reqs, doc, dv = setup_base(db, req_count=1)
    db.commit()
    
    status, gap = evaluate_sufficiency(db, r.id)
    assert status == "INSUFFICIENT"
    assert reqs[0].status == "NOT_COVERED"

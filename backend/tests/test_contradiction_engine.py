import os
import sys
import uuid
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app.db import SessionLocal
from app.models import RegulatoryQuery, Response, Claim, Contradiction
from app.validation.contradiction_engine import detect_contradictions, ContradictionOutput

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def setup_claims(db):
    # Setup historical approved response
    q1 = RegulatoryQuery(query_text="Old query")
    db.add(q1)
    db.flush()
    r1 = Response(query_id=q1.id, status="approved")
    db.add(r1)
    db.flush()
    c1 = Claim(response_id=r1.id, claim_code="CLM-OLD", claim_text="Old claim", product_topic="topic-X")
    db.add(c1)
    
    # Setup new draft response
    q2 = RegulatoryQuery(query_text="New query")
    db.add(q2)
    db.flush()
    r2 = Response(query_id=q2.id, status="draft")
    db.add(r2)
    db.flush()
    c2 = Claim(response_id=r2.id, claim_code="CLM-NEW", claim_text="New claim", product_topic="topic-X")
    db.add(c2)
    
    # Setup unrelated claim
    c3 = Claim(response_id=r1.id, claim_code="CLM-OTHER", claim_text="Other topic", product_topic="topic-Y")
    db.add(c3)
    
    db.flush()
    return c2.id, c1.id

@patch("app.validation.contradiction_engine.call_with_retry_and_fallback")
def test_detect_contradiction_likely(mock_llm, db_session):
    mock_llm.return_value = ContradictionOutput(
        classification="LIKELY_CONTRADICTION",
        reasoning="Blatant conflict.",
        distinguishing_factors_considered=[]
    )
    
    new_claim_id, old_claim_id = setup_claims(db_session)
    detect_contradictions(db_session, new_claim_id)
    
    contras = db_session.query(Contradiction).filter(Contradiction.claim_a_id == new_claim_id).all()
    assert len(contras) == 1
    assert contras[0].claim_b_id == old_claim_id
    assert contras[0].classification == "LIKELY_CONTRADICTION"

@patch("app.validation.contradiction_engine.call_with_retry_and_fallback")
def test_detect_contradiction_compatible(mock_llm, db_session):
    mock_llm.return_value = ContradictionOutput(
        classification="COMPATIBLE",
        reasoning="All good.",
        distinguishing_factors_considered=[]
    )
    
    new_claim_id, old_claim_id = setup_claims(db_session)
    detect_contradictions(db_session, new_claim_id)
    
    contras = db_session.query(Contradiction).filter(Contradiction.claim_a_id == new_claim_id).all()
    assert len(contras) == 0

def test_no_candidates(db_session):
    q = RegulatoryQuery(query_text="Lonely query")
    db_session.add(q)
    db_session.flush()
    r = Response(query_id=q.id, status="draft")
    db_session.add(r)
    db_session.flush()
    c = Claim(response_id=r.id, claim_code="CLM-LONELY", claim_text="Alone", product_topic="topic-LONE")
    db_session.add(c)
    db_session.flush()
    
    # Should exit cleanly without calling LLM
    detect_contradictions(db_session, c.id)
    contras = db_session.query(Contradiction).filter(Contradiction.claim_a_id == c.id).all()
    assert len(contras) == 0

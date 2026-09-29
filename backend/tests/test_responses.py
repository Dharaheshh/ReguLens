import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db import SessionLocal
from app.models import RegulatoryQuery, Response, AuditEvent

client = TestClient(app)

@pytest.fixture
def test_response_id():
    db = SessionLocal()
    try:
        q = RegulatoryQuery(query_text="Test query")
        db.add(q)
        db.flush()
        r = Response(query_id=q.id, draft_text="Draft", status="draft")
        db.add(r)
        db.commit()
        return r.id
    finally:
        db.close()

def test_get_response(test_response_id):
    res = client.get(f"/api/v1/responses/{test_response_id}")
    assert res.status_code == 200
    assert res.json()["response_id"] == str(test_response_id)
    assert res.json()["draft_text"] == "Draft"

def test_patch_response(test_response_id):
    res = client.patch(f"/api/v1/responses/{test_response_id}", json={"draft_text": "Edited draft"})
    assert res.status_code == 200
    assert res.json()["draft_text"] == "Edited draft"
    
    # Verify in DB
    db = SessionLocal()
    r = db.query(Response).filter(Response.id == test_response_id).first()
    assert r.draft_text == "Edited draft"
    db.close()

def test_approve_response(test_response_id):
    res = client.post(f"/api/v1/responses/{test_response_id}/approve", json={"reviewed_by": "test_user"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "approved"
    
    # Check audit
    db = SessionLocal()
    r = db.query(Response).filter(Response.id == test_response_id).first()
    assert r.status == "approved"
    assert r.reviewed_by == "test_user"
    assert r.reviewed_at is not None
    
    audit = db.query(AuditEvent).filter(AuditEvent.response_id == test_response_id).first()
    assert audit is not None
    assert audit.event_type == "response_approved"
    assert audit.actor == "test_user"
    db.close()

def test_reject_response():
    db = SessionLocal()
    q = RegulatoryQuery(query_text="Test reject")
    db.add(q)
    db.flush()
    r = Response(query_id=q.id, draft_text="Draft", status="draft")
    db.add(r)
    db.commit()
    r_id = r.id
    db.close()
    
    res = client.post(f"/api/v1/responses/{r_id}/reject", json={"reviewed_by": "test_user", "reason": "Bad draft"})
    assert res.status_code == 200
    assert res.json()["status"] == "rejected"
    
    db = SessionLocal()
    audit = db.query(AuditEvent).filter(AuditEvent.response_id == r_id).first()
    assert audit.event_type == "response_rejected"
    assert audit.payload["reason"] == "Bad draft"
    db.close()

def test_get_audit(test_response_id):
    client.post(f"/api/v1/responses/{test_response_id}/approve", json={"reviewed_by": "test_user"})
    
    res = client.get(f"/api/v1/responses/{test_response_id}/audit")
    assert res.status_code == 200
    events = res.json()["events"]
    assert len(events) == 1
    assert events[0]["event_type"] == "response_approved"
    assert events[0]["actor"] == "test_user"

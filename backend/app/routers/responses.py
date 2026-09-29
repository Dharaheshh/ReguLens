"""Response Review Endpoints - TASK-018.

GET /api/v1/responses/{id}
PATCH /api/v1/responses/{id}
POST /api/v1/responses/{id}/approve
POST /api/v1/responses/{id}/reject
GET /api/v1/responses/{id}/audit
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Response, AuditEvent
from app.schemas import (
    QueryResponse,
    ResponsePatchRequest,
    ResponseApproveRequest,
    ResponseRejectRequest,
    ResponseReviewResponse,
    AuditEventsResponse,
    AuditEventItem
)
from app.routers.queries import build_query_response

router = APIRouter(prefix="/api/v1", tags=["responses"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/responses/{response_id}", response_model=QueryResponse)
def get_response(response_id: uuid.UUID, db: Session = Depends(get_db)):
    """Full detail view for the review screen."""
    resp = db.query(Response).filter(Response.id == response_id).first()
    if not resp:
        raise HTTPException(status_code=404, detail="Response not found")
        
    return build_query_response(db, resp.query_id)


@router.patch("/responses/{response_id}", response_model=QueryResponse)
def patch_response(
    response_id: uuid.UUID,
    request: ResponsePatchRequest,
    db: Session = Depends(get_db)
):
    """Edit the draft text before approval."""
    resp = db.query(Response).filter(Response.id == response_id).first()
    if not resp:
        raise HTTPException(status_code=404, detail="Response not found")
        
    if resp.status != "draft":
        raise HTTPException(status_code=400, detail="Cannot edit a non-draft response")
        
    resp.draft_text = request.draft_text
    db.commit()
    
    return build_query_response(db, resp.query_id)


@router.post("/responses/{response_id}/approve", response_model=ResponseReviewResponse)
def approve_response(
    response_id: uuid.UUID,
    request: ResponseApproveRequest,
    db: Session = Depends(get_db)
):
    """Human approval action."""
    resp = db.query(Response).filter(Response.id == response_id).first()
    if not resp:
        raise HTTPException(status_code=404, detail="Response not found")
        
    if resp.status == "approved":
        raise HTTPException(status_code=400, detail="Response is already approved")
        
    now = datetime.now(timezone.utc)
    resp.status = "approved"
    resp.reviewed_by = request.reviewed_by
    resp.reviewed_at = now
    
    # Create audit event
    audit = AuditEvent(
        event_type="response_approved",
        response_id=resp.id,
        actor=request.reviewed_by,
        payload={}
    )
    db.add(audit)
    db.commit()
    
    return ResponseReviewResponse(
        response_id=resp.id,
        status=resp.status,
        version=resp.version,
        reviewed_at=resp.reviewed_at.isoformat() if resp.reviewed_at else None
    )


@router.post("/responses/{response_id}/reject", response_model=ResponseReviewResponse)
def reject_response(
    response_id: uuid.UUID,
    request: ResponseRejectRequest,
    db: Session = Depends(get_db)
):
    """Human rejection action."""
    resp = db.query(Response).filter(Response.id == response_id).first()
    if not resp:
        raise HTTPException(status_code=404, detail="Response not found")
        
    if resp.status == "rejected":
        raise HTTPException(status_code=400, detail="Response is already rejected")
        
    now = datetime.now(timezone.utc)
    resp.status = "rejected"
    resp.reviewed_by = request.reviewed_by
    resp.reviewed_at = now
    
    # Create audit event
    audit = AuditEvent(
        event_type="response_rejected",
        response_id=resp.id,
        actor=request.reviewed_by,
        payload={"reason": request.reason} if request.reason else {}
    )
    db.add(audit)
    db.commit()
    
    return ResponseReviewResponse(
        response_id=resp.id,
        status=resp.status,
        version=resp.version,
        reviewed_at=resp.reviewed_at.isoformat() if resp.reviewed_at else None
    )


@router.get("/responses/{response_id}/audit", response_model=AuditEventsResponse)
def get_response_audit(
    response_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get audit trail for a response."""
    resp = db.query(Response).filter(Response.id == response_id).first()
    if not resp:
        raise HTTPException(status_code=404, detail="Response not found")
        
    events = db.query(AuditEvent).filter(AuditEvent.response_id == response_id).order_by(AuditEvent.created_at).all()
    
    event_items = []
    for ev in events:
        event_items.append(AuditEventItem(
            event_type=ev.event_type,
            actor=ev.actor,
            payload=ev.payload,
            created_at=ev.created_at.isoformat()
        ))
        
    return AuditEventsResponse(events=event_items)

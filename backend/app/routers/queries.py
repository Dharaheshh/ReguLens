"""Query Orchestration - TASK-014.

POST /api/v1/queries
"""
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import (
    RegulatoryQuery, Requirement, RequirementEvidence, Response, Claim,
    Citation, Evidence, Chunk, Document
)
from app.schemas import (
    QueryRequest, QueryResponse, RequirementResponse, ClaimResponse,
    EvidenceCitationResponse
)
from app.generation.requirement_extraction import extract_requirements
from app.retrieval.hybrid_search import hybrid_search
from app.generation.response_generation import generate_response
from app.validation.citation_validator import validate_citations
from app.llm.provider import LLMCallError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["queries"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/queries", response_model=QueryResponse)
def submit_query(
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    """Run the full query pipeline."""
    if not request.query_text or not request.query_text.strip():
        raise HTTPException(status_code=400, detail="Query text cannot be empty.")
        
    query_text = request.query_text.strip()
    
    # 1. Create and persist query
    query = RegulatoryQuery(query_text=query_text)
    db.add(query)
    db.flush()
    
    try:
        # 2. Extract structured requirements
        requirements = extract_requirements(db, query.id, query_text)
        
        # 3. Retrieve evidence for each requirement
        evidence_pack = []
        evidence_pack_dedup = set()
        
        for req in requirements:
            search_query = f"{req.description} {' '.join(req.keywords)}"
            results = hybrid_search(db, search_query, k=5)
            
            for result in results:
                if result.evidence_id:
                    # Persist requirement_evidence relationship
                    req_evd = RequirementEvidence(
                        requirement_id=req.id,
                        evidence_id=result.evidence_id,
                        retrieval_score=result.score
                    )
                    # We might retrieve the same evidence for different requirements,
                    # so handle unique constraint violations if we fetch the same one.
                    # Or just query first:
                    existing = db.query(RequirementEvidence).filter(
                        RequirementEvidence.requirement_id == req.id,
                        RequirementEvidence.evidence_id == result.evidence_id
                    ).first()
                    if not existing:
                        db.add(req_evd)
                    
                    if result.evidence_code not in evidence_pack_dedup:
                        evidence_pack.append({
                            "evidence_code": result.evidence_code,
                            "text": result.content,
                            "source_type": result.source_type if hasattr(result, "source_type") else "unknown"
                        })
                        evidence_pack_dedup.add(result.evidence_code)
                        
        db.flush()
        
        if not evidence_pack:
            logger.warning("No evidence retrieved for query %s", query.id)
            # Empty evidence pack is okay, generation will handle it.
            
        # 4. Generate response
        req_dicts = [{"req_code": r.req_code, "description": r.description} for r in requirements]
        response, claims = generate_response(db, query.id, query_text, req_dicts, evidence_pack)
        
        # 5. Resolve proposed citations and validate semantics
        from app.validation.claim_validator import validate_claim_semantics
        for claim in claims:
            validate_citations(db, claim.id, getattr(claim, "_cited_evidence_codes", []))
            validate_claim_semantics(db, claim.id)
            
        db.commit()
        
    except LLMCallError as e:
        db.rollback()
        # If generation fails, we should still return a 500 per the contract
        raise HTTPException(status_code=500, detail={"code": "LLM_FAILED", "message": str(e)})
    except Exception as e:
        db.rollback()
        logger.exception("Pipeline failed")
        raise HTTPException(status_code=500, detail={"code": "PIPELINE_FAILED", "message": str(e)})

    # Build response structure
    return build_query_response(db, query.id)


@router.get("/queries/{query_id}", response_model=QueryResponse)
def get_query(
    query_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    return build_query_response(db, query_id)


def build_query_response(db: Session, query_id: uuid.UUID) -> dict:
    """Helper to construct the API response for a query."""
    query = db.query(RegulatoryQuery).filter(RegulatoryQuery.id == query_id).first()
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
        
    response = db.query(Response).filter(Response.query_id == query_id).order_by(Response.created_at.desc()).first()
    requirements = db.query(Requirement).filter(Requirement.query_id == query_id).order_by(Requirement.req_code).all()
    
    req_list = []
    for r in requirements:
        req_list.append({
            "req_code": r.req_code,
            "description": r.description,
            "status": r.status
        })
        
    res_dict = {
        "query_id": query.id,
        "requirements": req_list,
        "claims": [],
        "contradictions": [],
    }
    
    if response:
        res_dict["response_id"] = response.id
        res_dict["draft_text"] = response.draft_text
        res_dict["sufficiency_status"] = response.sufficiency_status
        res_dict["gap_summary"] = response.gap_summary
        res_dict["status"] = response.status
        
        claims = db.query(Claim).filter(Claim.response_id == response.id).order_by(Claim.claim_code).all()
        for c in claims:
            citations = db.query(Citation).filter(Citation.claim_id == c.id).all()
            cit_list = []
            for cit in citations:
                evd = db.query(Evidence).filter(Evidence.id == cit.evidence_id).first()
                if evd:
                    chunk = db.query(Chunk).filter(Chunk.id == evd.chunk_id).first()
                    doc = db.query(Document).filter(Document.id == evd.document_id).first()
                    cit_list.append({
                        "evidence_id": evd.id,
                        "evidence_code": evd.evidence_code,
                        "document": doc.filename if doc else None,
                        "page_start": chunk.page_start if chunk else None,
                        "page_end": chunk.page_end if chunk else None,
                        "section": chunk.section if chunk else None
                    })
            
            res_dict["claims"].append({
                "claim_id": c.id,
                "claim_code": c.claim_code,
                "claim_text": c.claim_text,
                "validation_state": c.validation_state,
                "citations": cit_list
            })
            
    return res_dict

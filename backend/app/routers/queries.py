"""Query endpoints - TASK-014.

POST /api/v1/queries
GET  /api/v1/queries/{query_id}
"""
import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import (
    RegulatoryQuery, Response as ResponseModel, Requirement, Claim, Citation, Evidence,
    Chunk, DocumentVersion, Document, RequirementEvidence
)
from app.schemas import (
    QueryCreate, QueryResponse, RequirementResponseItem, ClaimResponseItem, CitationResponseItem
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


def _build_query_response(db: Session, query_id: uuid.UUID) -> QueryResponse:
    """Helper to assemble the QueryResponse from DB state."""
    query = db.query(RegulatoryQuery).filter(RegulatoryQuery.id == query_id).first()
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")

    response = db.query(ResponseModel).filter(
        ResponseModel.query_id == query_id
    ).order_by(ResponseModel.created_at.desc()).first()
    
    if not response:
        raise HTTPException(status_code=404, detail="No response generated for query")

    # Get requirements
    db_reqs = db.query(Requirement).filter(Requirement.query_id == query_id).order_by(Requirement.req_code).all()
    req_items = [
        RequirementResponseItem(
            req_code=r.req_code,
            description=r.description,
            status=r.status
        ) for r in db_reqs
    ]

    # Get claims and citations
    db_claims = db.query(Claim).filter(Claim.response_id == response.id).order_by(Claim.claim_code).all()
    claim_items = []
    for c in db_claims:
        db_citations = db.query(Citation).filter(
            Citation.claim_id == c.id, 
            Citation.validated == True
        ).all()
        
        cit_items = []
        for cit in db_citations:
            # Need to get Evidence -> Chunk -> DocumentVersion -> Document
            evidence = db.query(Evidence).filter(Evidence.id == cit.evidence_id).first()
            if not evidence:
                continue
                
            chunk = db.query(Chunk).filter(Chunk.id == evidence.chunk_id).first()
            doc = db.query(Document).filter(Document.id == evidence.document_id).first()
            
            cit_items.append(CitationResponseItem(
                evidence_id=cit.evidence_id,
                evidence_code=evidence.evidence_code,
                document=doc.filename if doc else None,
                page_start=chunk.page_start if chunk else None,
                page_end=chunk.page_end if chunk else None,
                section=chunk.section if chunk else None
            ))
            
        claim_items.append(ClaimResponseItem(
            claim_id=c.id,
            claim_code=c.claim_code,
            claim_text=c.claim_text,
            validation_state=c.validation_state,
            citations=cit_items
        ))

    # Return empty list for contradictions for now (TASK-017)
    return QueryResponse(
        query_id=query.id,
        response_id=response.id,
        draft_text=response.draft_text,
        sufficiency_status=response.sufficiency_status,
        gap_summary=response.gap_summary,
        requirements=req_items,
        claims=claim_items,
        contradictions=[],
        status=response.status
    )


@router.post("/queries", response_model=QueryResponse, status_code=200)
def create_query(query_data: QueryCreate, db: Session = Depends(get_db)):
    """Submit a query and run canonical pipeline stages 1-7."""
    query_text = query_data.query_text.strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="Query text cannot be empty")

    # Stage 1: Normalize & persist query
    query = RegulatoryQuery(query_text=query_text)
    db.add(query)
    db.commit()
    db.refresh(query)
    
    # Let's track if we hit a critical failure
    try:
        # Stage 2: Requirement extraction
        try:
            requirements = extract_requirements(db, query.id, query.query_text)
        except Exception as e:
            logger.exception("Failed to extract requirements")
            raise HTTPException(status_code=500, detail="LLM_FAILED")
            
        # Stage 3-5: Retrieval & Evidence Pack Assembly
        evidence_pack = []
        for req in requirements:
            search_query = f"{req.description} {' '.join(req.keywords)}"
            try:
                results = hybrid_search(db, search_query, k=5)
                if not results:
                    req.status = "NOT_COVERED"
                    db.add(req)
                else:
                    req.status = "COVERED" # basic naive assignment until TASK-016
                    db.add(req)
                    
                for r in results:
                    if r.evidence_id and r.evidence_code:
                        # Add to requirement_evidence join table
                        join_row = RequirementEvidence(
                            requirement_id=req.id,
                            evidence_id=r.evidence_id,
                            retrieval_score=r.score
                        )
                        db.add(join_row)
                        
                        # Add to pack
                        evidence_pack.append({
                            "evidence_code": r.evidence_code,
                            "text": r.content,
                            "source_type": "unknown" # not needed strictly by LLM
                        })
            except Exception as e:
                logger.exception(f"Retrieval failed for req {req.req_code}")
                req.status = "NOT_COVERED"
                db.add(req)
                # Don't fail the whole pipeline just because one retrieval failed

        db.flush()
        
        # Deduplicate evidence pack
        seen_codes = set()
        unique_evidence_pack = []
        for e in evidence_pack:
            if e["evidence_code"] not in seen_codes:
                seen_codes.add(e["evidence_code"])
                unique_evidence_pack.append(e)

        # Stage 6: Response generation
        req_dicts = [{"req_code": r.req_code, "description": r.description} for r in requirements]
        try:
            response, claims = generate_response(
                db=db,
                query_id=query.id,
                query_text=query.query_text,
                requirements=req_dicts,
                evidence_pack=unique_evidence_pack
            )
        except LLMCallError as e:
            # LLM failed completely
            resp = ResponseModel(query_id=query.id, status="LLM_FAILED")
            db.add(resp)
            db.commit()
            raise HTTPException(status_code=500, detail="LLM_FAILED")
            
        # Stage 7: Citation Validation
        for claim in claims:
            validate_citations(db, claim.id, claim._cited_evidence_codes)
            
        db.commit()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Pipeline failed unexpectedly")
        db.rollback()
        raise HTTPException(status_code=500, detail="PIPELINE_FAILED")
        
    return _build_query_response(db, query.id)


@router.get("/queries/{query_id}", response_model=QueryResponse)
def get_query(query_id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieve a previously run query."""
    return _build_query_response(db, query_id)

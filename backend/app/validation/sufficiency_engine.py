"""Evidence Sufficiency Engine - TASK-016.

Deterministically calculates whether retrieved evidence is sufficient to answer
the extracted requirements. Updates Requirement and Response statuses.
"""
import logging
import uuid
from typing import Literal

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Requirement, RequirementEvidence, Response

logger = logging.getLogger(__name__)

# Configurable thresholds for RRF score
# Fused RRF scores in our implementation typically max out around 0.033
THRESHOLD_HIGH = 0.015
THRESHOLD_LOW = 0.005


def run_sufficiency_check(db: Session, query_id: uuid.UUID) -> None:
    """Calculate sufficiency based on requirement_evidence scores.
    
    Updates:
    - Requirement.status (COVERED, PARTIALLY_COVERED, NOT_COVERED)
    - Response.sufficiency_status (SUFFICIENT, PARTIALLY_SUFFICIENT, INSUFFICIENT)
    - Response.gap_summary (string)
    """
    requirements = db.query(Requirement).filter(Requirement.query_id == query_id).all()
    if not requirements:
        logger.warning(f"No requirements found for query {query_id}")
        return

    req_statuses = []
    gap_lines = []

    for req in requirements:
        evd_records = db.query(RequirementEvidence).filter(
            RequirementEvidence.requirement_id == req.id
        ).all()
        
        match_count = len(evd_records)
        top_score = max([e.retrieval_score for e in evd_records]) if evd_records else 0.0

        if top_score >= THRESHOLD_HIGH and match_count >= 2:
            req.status = "COVERED"
        elif top_score >= THRESHOLD_LOW:
            req.status = "PARTIALLY_COVERED"
        else:
            req.status = "NOT_COVERED"
            
        req_statuses.append(req.status)
        
        if req.status == "NOT_COVERED":
            gap_lines.append(f"{req.req_code} ({req.description}) is not covered.")
        elif req.status == "PARTIALLY_COVERED":
            gap_lines.append(f"{req.req_code} ({req.description}) is only partially covered.")

    # Overall response status
    if all(s == "COVERED" for s in req_statuses):
        overall = "SUFFICIENT"
    elif any(s == "NOT_COVERED" for s in req_statuses):
        overall = "INSUFFICIENT"
    else:
        # At least one PARTIALLY_COVERED, and none NOT_COVERED
        overall = "PARTIALLY_SUFFICIENT"

    response = db.query(Response).filter(Response.query_id == query_id).first()
    if response:
        response.sufficiency_status = overall
        response.gap_summary = "\n".join(gap_lines) if gap_lines else None
        
    db.flush()
    logger.info(f"Query {query_id} sufficiency set to {overall}")

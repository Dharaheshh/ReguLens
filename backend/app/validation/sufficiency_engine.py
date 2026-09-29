"""Evidence Sufficiency Engine (TASK-016).

Fully deterministic engine. Aggregates requirement coverage based on
retrieval scores, and computes overall response sufficiency.
"""
from typing import Tuple
from sqlalchemy.orm import Session

from app.models import Response, Requirement, RequirementEvidence

# RRF scores (1 / (60 + rank)). Rank 1 gives ~0.01639.
THRESHOLD_HIGH = 0.015
THRESHOLD_LOW = 0.010

def evaluate_sufficiency(db: Session, response_id: str) -> Tuple[str, str]:
    """Evaluate sufficiency of evidence for a response.

    Updates the response and requirement statuses in the DB.

    Args:
        db: SQLAlchemy session
        response_id: UUID of the Response

    Returns:
        (sufficiency_status, gap_summary)
    """
    response = db.query(Response).filter(Response.id == response_id).first()
    if not response:
        raise ValueError(f"Response {response_id} not found")

    requirements = db.query(Requirement).filter(Requirement.query_id == response.query_id).order_by(Requirement.req_code).all()
    
    if not requirements:
        response.sufficiency_status = "INSUFFICIENT"
        response.gap_summary = "No requirements were extracted to evaluate sufficiency."
        db.add(response)
        db.flush()
        return response.sufficiency_status, response.gap_summary

    all_covered = True
    any_not_covered = False
    gap_lines = []

    for req in requirements:
        req_evidences = db.query(RequirementEvidence).filter(
            RequirementEvidence.requirement_id == req.id
        ).all()

        if not req_evidences:
            top_score = 0.0
            match_count = 0
        else:
            top_score = max(re.retrieval_score for re in req_evidences)
            match_count = len(req_evidences)

        if top_score >= THRESHOLD_HIGH and match_count >= 2:
            req.status = "COVERED"
        elif top_score >= THRESHOLD_LOW:
            req.status = "PARTIALLY_COVERED"
        else:
            req.status = "NOT_COVERED"

        if req.status == "NOT_COVERED":
            any_not_covered = True
            all_covered = False
            gap_lines.append(f"{req.req_code} is not covered by retrieved evidence.")
        elif req.status == "PARTIALLY_COVERED":
            all_covered = False
            gap_lines.append(f"{req.req_code} is only partially covered (insufficient high-confidence matches).")
            
        db.add(req)

    if all_covered:
        sufficiency_status = "SUFFICIENT"
        gap_summary = "All requirements are sufficiently covered by evidence."
    elif any_not_covered:
        sufficiency_status = "INSUFFICIENT"
        gap_summary = " ".join(gap_lines)
    else:
        sufficiency_status = "PARTIALLY_SUFFICIENT"
        gap_summary = " ".join(gap_lines)

    response.sufficiency_status = sufficiency_status
    response.gap_summary = gap_summary
    db.add(response)
    db.flush()
    
    return sufficiency_status, gap_summary

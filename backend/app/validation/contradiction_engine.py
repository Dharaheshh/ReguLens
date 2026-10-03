"""Contradiction Detection Engine - TASK-017.

Identifies potential contradictions between new claims and approved historical claims.
"""
import logging
import uuid
from typing import Literal

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models import Claim, Response, Contradiction, DocumentVersion, Citation, Evidence
from app.llm.provider import call_with_retry_and_fallback

logger = logging.getLogger(__name__)


class ContradictionOutput(BaseModel):
    classification: Literal["COMPATIBLE", "POTENTIAL_CONTRADICTION", "LIKELY_CONTRADICTION", "INSUFFICIENT_CONTEXT"]
    reasoning: str
    distinguishing_factors_considered: list[str]


def detect_contradictions(db: Session, current_claim_id: uuid.UUID) -> None:
    """Check a new claim against historical approved claims for the same topic.
    
    Args:
        db: SQLAlchemy session.
        current_claim_id: UUID of the newly generated claim.
    """
    claim = db.query(Claim).filter(Claim.id == current_claim_id).first()
    if not claim:
        logger.warning(f"Claim {current_claim_id} not found.")
        return

    # Find candidates: approved responses, same product_topic, exclude current
    candidates = (
        db.query(Claim)
        .join(Response, Claim.response_id == Response.id)
        .filter(
            Claim.product_topic == claim.product_topic,
            Response.status == "approved",
            Claim.id != claim.id
        )
        .order_by(Response.created_at.desc())
        .limit(10)
        .all()
    )

    if not candidates:
        logger.info(f"No historical candidates found for claim {current_claim_id}")
        return

    # Get document version date helper
    def get_latest_doc_version(c: Claim) -> str:
        cit = db.query(Citation).filter(Citation.claim_id == c.id).first()
        if not cit:
            return "unknown"
        evd = db.query(Evidence).filter(Evidence.id == cit.evidence_id).first()
        if not evd:
            return "unknown"
        ver = db.query(DocumentVersion).filter(DocumentVersion.id == evd.document_version_id).first()
        return str(ver.version_number) if ver else "unknown"

    new_version = get_latest_doc_version(claim)

    for cand in candidates:
        cand_version = get_latest_doc_version(cand)

        system_prompt = (
            "You are an expert regulatory safety reviewer.\n"
            "Your task is to compare a new generated claim against a historical approved claim "
            "and determine if they contradict each other.\n"
            "You must output ONLY JSON matching the requested schema.\n"
            "The output MUST contain 'classification', 'reasoning', and 'distinguishing_factors_considered'.\n\n"
            "Example Output:\n"
            "{\n"
            "  \"classification\": \"COMPATIBLE\",\n"
            "  \"reasoning\": \"The claims discuss different components.\",\n"
            "  \"distinguishing_factors_considered\": [\"scope\"]\n"
            "}\n\n"
            "Rules:\n"
            "- COMPATIBLE: No conflict, or they discuss different scopes.\n"
            "- POTENTIAL_CONTRADICTION: They appear to conflict but details are ambiguous.\n"
            "- LIKELY_CONTRADICTION: They clearly conflict on a material fact.\n"
            "- INSUFFICIENT_CONTEXT: Impossible to compare.\n"
            "Consider distinguishing factors like date, version, scope, units, thresholds.\n"
        )

        user_prompt = (
            f"New Claim (Version {new_version}, Date {claim.created_at.date()}):\n"
            f"{claim.claim_text}\n\n"
            f"Historical Claim (Version {cand_version}, Date {cand.created_at.date()}):\n"
            f"{cand.claim_text}\n\n"
            "Classify the relationship between these claims."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            result = call_with_retry_and_fallback(
                system_prompt=system_prompt,
                user_content=user_prompt,
                response_model=ContradictionOutput,
                temperature=0.0
            )
            
            if result.classification != "COMPATIBLE":
                contra = Contradiction(
                    claim_a_id=claim.id,
                    claim_b_id=cand.id,
                    classification=result.classification,
                    reasoning=result.reasoning
                )
                db.add(contra)
                logger.info(f"Contradiction detected ({result.classification}) between {claim.id} and {cand.id}")
                
        except Exception as e:
            logger.error(f"Contradiction check failed for pair {claim.id} - {cand.id}: {e}")
            # Continue checking other candidates
            continue
            
    db.flush()

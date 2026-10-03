"""Claim ↔ Evidence Validation - TASK-015.

Uses an LLM to semantically validate whether a claim is actually supported by
the specific evidence chunks it cited. Deterministic checks happen first.
"""
import logging
import uuid
from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.models import Claim, Citation, Evidence, Chunk
from app.llm.provider import call_with_retry_and_fallback

logger = logging.getLogger(__name__)


class SemanticValidationOutput(BaseModel):
    validation_state: Literal["SUPPORTED", "PARTIALLY_SUPPORTED", "UNSUPPORTED", "OVERCLAIM"]
    reasoning: str
    supported_portion: str | None = None


def validate_claim_semantics(db: Session, claim_id: uuid.UUID) -> SemanticValidationOutput | None:
    """Validate a single claim against its cited evidence using the LLM.

    Args:
        db: SQLAlchemy session.
        claim_id: The UUID of the claim to validate.

    Returns:
        The SemanticValidationOutput from the LLM, or None if validation 
        was skipped deterministically (e.g., no citations).
    """
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        logger.warning(f"Claim {claim_id} not found.")
        return None

    if claim.validation_state == "UNSUPPORTED":
        # Deterministically marked as unsupported (e.g., by citation_validator.py)
        logger.info(f"Claim {claim_id} is already deterministically UNSUPPORTED. Skipping semantic check.")
        return None

    # Fetch cited evidence
    citations = db.query(Citation).filter(Citation.claim_id == claim_id, Citation.validated == True).all()
    if not citations:
        # No valid citations found
        claim.validation_state = "UNSUPPORTED"
        claim.validation_reasoning = "No valid cited evidence found."
        db.flush()
        return SemanticValidationOutput(
            validation_state="UNSUPPORTED",
            reasoning="No valid cited evidence found."
        )

    evidence_pack = []
    for cit in citations[:3]:
        evd = db.query(Evidence).filter(Evidence.id == cit.evidence_id).first()
        if evd:
            chunk = db.query(Chunk).filter(Chunk.id == evd.chunk_id).first()
            if chunk:
                text = chunk.content
                if len(text) > 900:
                    text = text[:900].rsplit(" ", 1)[0] + "..."
                evidence_pack.append({
                    "evidence_code": evd.evidence_code,
                    "text": text,
                    "source_type": evd.source_type
                })

    if not evidence_pack:
        claim.validation_state = "UNSUPPORTED"
        claim.validation_reasoning = "Evidence chunks could not be retrieved."
        db.flush()
        return SemanticValidationOutput(
            validation_state="UNSUPPORTED",
            reasoning="Evidence chunks could not be retrieved."
        )

    # Prompt construction
    evidence_str = "\n".join([
        f"--- Evidence {e['evidence_code']} ({e['source_type']}) ---\n{e['text']}\n"
        for e in evidence_pack
    ])

    system_prompt = (
        "You are an expert regulatory validation engine. Your task is to determine whether "
        "the provided claim is factually supported by the specific provided evidence.\n"
        "You must output ONLY JSON matching the requested schema.\n"
        "The output MUST contain the exact key 'validation_state' and 'reasoning'. Do NOT use 'verdict' or 'evaluation'.\n\n"
        "Example Output:\n"
        "{\n"
        "  \"validation_state\": \"SUPPORTED\",\n"
        "  \"reasoning\": \"The evidence clearly supports the claim...\"\n"
        "}\n\n"
        "Rules:\n"
        "- SUPPORTED: The claim is fully backed by the evidence.\n"
        "- PARTIALLY_SUPPORTED: Some aspects are supported, others are missing.\n"
        "- OVERCLAIM: The claim states things beyond what the evidence proves (exaggeration).\n"
        "- UNSUPPORTED: The evidence does not support the claim at all, or contradicts it.\n"
    )

    user_prompt = (
        f"Claim text: {claim.claim_text}\n\n"
        "Provided Evidence:\n"
        f"{evidence_str}\n\n"
        "Evaluate the claim based ONLY on the evidence above."
    )

    try:
        result = call_with_retry_and_fallback(
            system_prompt=system_prompt,
            user_content=user_prompt,
            response_model=SemanticValidationOutput,
            temperature=0.0
        )
        
        claim.validation_state = result.validation_state
        claim.validation_reasoning = result.reasoning
        db.flush()
        return result
    except Exception as e:
        logger.error(f"Semantic validation failed for claim {claim_id}: {e}")
        # In case of LLM failure, we don't automatically mark as unsupported to avoid 
        # overwriting valid claims. The status remains pending/None or whatever it was.
        raise

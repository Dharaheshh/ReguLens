"""Claim <-> Evidence Validation (TASK-015).

LLM Call 3 determines if a claim is actually supported by its cited evidence.
"""
import logging
import uuid
from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.models import Claim, Citation, Evidence, Chunk
from app.llm.provider import call_with_retry_and_fallback, LLMCallError

logger = logging.getLogger(__name__)

class ClaimValidationOutput(BaseModel):
    validation_state: Literal["SUPPORTED", "PARTIALLY_SUPPORTED", "OVERCLAIM", "CONFLICTING", "UNSUPPORTED"]
    reasoning: str
    supported_portion: str


SYSTEM_PROMPT = """You are a rigorous scientific and regulatory claim validator.
Your job is to determine if a specific claim is supported by the provided evidence.

You will receive a claim and a list of evidence excerpts that the claim cites.
You MUST NOT evaluate the claim using outside knowledge. Evaluate strictly based on the provided evidence text.

Classify the claim into ONE of these states:
- SUPPORTED: The evidence fully backs the claim as written.
- PARTIALLY_SUPPORTED: The evidence supports part of the claim, but not all of it.
- OVERCLAIM: The claim goes further than the evidence allows (e.g. evidence says "below threshold", claim says "zero").
- CONFLICTING: The evidence directly contradicts the claim.
- UNSUPPORTED: The evidence is completely irrelevant or does not support the claim at all.

You must also provide:
- reasoning: A brief explanation of why you chose this state.
- supported_portion: A rewrite of the claim representing only what the evidence actually supports. If completely unsupported, state "None".

Return JSON matching the schema."""


def validate_claim(db: Session, claim_id: uuid.UUID) -> Claim:
    """Validate a claim against its cited evidence.

    Deterministic pre-check: if a claim has 0 validated citations, it becomes UNSUPPORTED.
    Otherwise, run LLM Call 3.

    Args:
        db: SQLAlchemy session
        claim_id: UUID of the claim to validate

    Returns:
        The updated Claim object.
    """
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise ValueError(f"Claim {claim_id} not found")

    # Get validated citations
    citations = db.query(Citation).filter(
        Citation.claim_id == claim.id,
        Citation.validated == True
    ).all()

    if not citations:
        claim.validation_state = "UNSUPPORTED"
        claim.validation_reasoning = "No validated citations available."
        db.add(claim)
        db.flush()
        return claim

    # Gather evidence
    evidence_items = []
    for cit in citations:
        evidence = db.query(Evidence).filter(Evidence.id == cit.evidence_id).first()
        if evidence:
            chunk = db.query(Chunk).filter(Chunk.id == evidence.chunk_id).first()
            if chunk:
                evidence_items.append({
                    "evidence_code": evidence.evidence_code,
                    "text": chunk.content,
                    "source_type": evidence.source_type
                })
                
    if not evidence_items:
        claim.validation_state = "UNSUPPORTED"
        claim.validation_reasoning = "Evidence text could not be resolved."
        db.add(claim)
        db.flush()
        return claim

    # Prepare LLM call
    user_content = f"""CLAIM:
{claim.claim_text}

CITED EVIDENCE:
"""
    for e in evidence_items:
        user_content += f"[{e['evidence_code']}] {e['text']}\n\n"

    try:
        output = call_with_retry_and_fallback(
            system_prompt=SYSTEM_PROMPT,
            user_content=user_content,
            response_model=ClaimValidationOutput,
            temperature=0.1
        )
        
        claim.validation_state = output.validation_state
        claim.validation_reasoning = output.reasoning
        # Note: the schema doesn't have a supported_portion field on the DB model,
        # but it is meant to be stored in validation_reasoning or we just log it.
        # Let's combine them into validation_reasoning for auditability.
        if output.validation_state != "SUPPORTED":
            claim.validation_reasoning += f" | Supported portion: {output.supported_portion}"
            
    except LLMCallError as e:
        logger.error(f"Claim validation LLM failed for claim {claim_id}: {e}")
        claim.validation_state = "VALIDATION_FAILED"
        claim.validation_reasoning = "LLM validation failed after retries."
        
    db.add(claim)
    db.flush()
    return claim

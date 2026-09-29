"""Citation Validator — TASK-013.

Fully deterministic — NO LLM call anywhere in this file.

Resolves proposed evidence codes against the evidence table.
- Found → creates a citations row (claim_id, evidence_id, validated=True).
- Not found → no citation row created.
- Zero valid citations → sets claim.validation_state = 'UNSUPPORTED'.
"""
import logging
import uuid

from sqlalchemy.orm import Session

from app.models import Evidence, Citation, Claim

logger = logging.getLogger(__name__)


def validate_citations(
    db: Session,
    claim_id: uuid.UUID,
    cited_evidence_codes: list[str],
) -> None:
    """Validate proposed evidence codes and create citation rows.

    For each code in cited_evidence_codes:
    - Look up evidence_code in the evidence table.
    - Found: create a citations row with validated=True.
    - Not found: skip — no citation row is created (per RULES.md rule #3-4).

    After processing all codes: if the claim has zero citation rows,
    set claim.validation_state = 'UNSUPPORTED' (per AI_RAG_DESIGN.md's
    deterministic pre-check).

    Args:
        db: SQLAlchemy session (caller manages commit/rollback).
        claim_id: UUID of the claim to validate citations for.
        cited_evidence_codes: List of evidence codes proposed by the LLM.
    """
    valid_count = 0

    for code in cited_evidence_codes:
        evidence = db.query(Evidence).filter(
            Evidence.evidence_code == code
        ).first()

        if evidence is not None:
            citation = Citation(
                claim_id=claim_id,
                evidence_id=evidence.id,
                validated=True,
            )
            db.add(citation)
            valid_count += 1
            logger.info("Citation validated: claim=%s, evidence=%s", claim_id, code)
        else:
            logger.warning(
                "Evidence code not found, skipping citation: claim=%s, code=%s",
                claim_id, code,
            )

    # Deterministic pre-check: zero validated citations → UNSUPPORTED
    if valid_count == 0:
        claim = db.query(Claim).filter(Claim.id == claim_id).first()
        if claim is not None:
            claim.validation_state = "UNSUPPORTED"
            logger.info(
                "Claim %s set to UNSUPPORTED (zero valid citations)", claim_id
            )

    db.flush()

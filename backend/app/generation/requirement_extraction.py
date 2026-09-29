"""Requirement Extraction — LLM Call 1 (TASK-011).

Decomposes a regulatory query into discrete, checkable requirements.
Uses LLMProvider from app.llm.provider.

Failure fallback (per AI_RAG_DESIGN.md): on total LLM failure after all
retries, treat the entire query text as a single REQ-01 requirement.
This is a LOCAL fallback — does not call the fallback LLM provider.
"""
import logging
import uuid

from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.llm.provider import call_with_retry_and_fallback, LLMCallError
from app.models import RegulatoryQuery, Requirement as RequirementModel

logger = logging.getLogger(__name__)


# ── Pydantic schemas per AI_RAG_DESIGN.md ──

class RequirementSchema(BaseModel):
    req_code: str
    description: str
    keywords: list[str]


class RequirementExtractionOutput(BaseModel):
    requirements: list[RequirementSchema]

    @field_validator("requirements")
    @classmethod
    def requirements_not_empty(cls, v: list[RequirementSchema]) -> list[RequirementSchema]:
        if not v:
            raise ValueError("requirements list must not be empty")
        return v


# ── System prompt ──

SYSTEM_PROMPT = """You are a regulatory requirements analyst. Your task is to decompose a regulatory query into discrete, individually checkable requirements.

For each requirement:
- Assign a sequential code (REQ-01, REQ-02, etc.)
- Write a clear, specific description of what evidence is needed
- List keywords that would help find relevant evidence in a document corpus

Respond with a JSON object matching this exact schema:
{
  "requirements": [
    {
      "req_code": "REQ-01",
      "description": "...",
      "keywords": ["keyword1", "keyword2"]
    }
  ]
}

Always extract at least one requirement. Be specific and actionable."""


def extract_requirements(
    db: Session,
    query_id: uuid.UUID,
    query_text: str,
) -> list[RequirementModel]:
    """Extract requirements from a regulatory query using LLM Call 1.

    Attempts LLM extraction with retry + fallback per CORRECTION-003.
    On total LLM failure, falls back to treating the entire query as a
    single REQ-01 requirement (per AI_RAG_DESIGN.md).

    Args:
        db: SQLAlchemy session.
        query_id: UUID of the regulatory_queries row.
        query_text: The query text to decompose.

    Returns:
        List of persisted Requirement model instances.
    """
    try:
        output = call_with_retry_and_fallback(
            system_prompt=SYSTEM_PROMPT,
            user_content=query_text,
            response_model=RequirementExtractionOutput,
            temperature=0.2,
        )
        requirements_data = output.requirements
        logger.info("LLM extracted %d requirements", len(requirements_data))

    except LLMCallError as e:
        # Local fallback: treat entire query as one requirement
        logger.warning(
            "All LLM attempts failed for requirement extraction, "
            "falling back to single-requirement mode: %s", e
        )
        requirements_data = [
            RequirementSchema(
                req_code="REQ-01",
                description=query_text,
                keywords=query_text.split()[:10],  # first 10 words as keywords
            )
        ]

    # Persist to database
    persisted: list[RequirementModel] = []
    for req in requirements_data:
        row = RequirementModel(
            query_id=query_id,
            req_code=req.req_code,
            description=req.description,
            keywords=req.keywords,
        )
        db.add(row)
        persisted.append(row)

    db.flush()
    return persisted

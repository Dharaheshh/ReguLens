"""Tests for Requirement Extraction — TASK-011 / LLM Call 1.

All tests use mocked LLM responses — no real network calls.
"""
import os
import sys
import json
import uuid
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app.db import SessionLocal
from app.models import RegulatoryQuery, Requirement as RequirementModel
from app.generation.requirement_extraction import (
    extract_requirements,
    RequirementExtractionOutput,
    RequirementSchema,
)
from app.llm.provider import LLMCallError


MICRO_QUERY = (
    "Provide evidence supporting the microbiological safety of the "
    "cultivated-cell product and describe the controls used during production."
)


def _create_query(db, text: str) -> RegulatoryQuery:
    """Helper to create a regulatory_queries row."""
    q = RegulatoryQuery(query_text=text)
    db.add(q)
    db.flush()
    return q


def test_extract_requirements_valid_llm_response():
    """Mock a valid LLM response → at least 2 requirements extracted and persisted."""
    mock_output = RequirementExtractionOutput(
        requirements=[
            RequirementSchema(
                req_code="REQ-01",
                description="Provide evidence of microbiological safety testing",
                keywords=["microbiological", "safety", "pathogen", "contamination"],
            ),
            RequirementSchema(
                req_code="REQ-02",
                description="Describe controls used during production",
                keywords=["controls", "production", "manufacturing", "quality"],
            ),
            RequirementSchema(
                req_code="REQ-03",
                description="Provide details on the cultivated-cell production process",
                keywords=["cultivated", "cell", "process", "production"],
            ),
        ]
    )

    db = SessionLocal()
    try:
        query = _create_query(db, MICRO_QUERY)

        with patch(
            "app.generation.requirement_extraction.call_with_retry_and_fallback",
            return_value=mock_output,
        ):
            reqs = extract_requirements(db, query.id, MICRO_QUERY)
            db.commit()

        assert len(reqs) >= 2
        assert all(isinstance(r, RequirementModel) for r in reqs)

        # Verify persistence
        persisted = db.query(RequirementModel).filter(
            RequirementModel.query_id == query.id
        ).all()
        assert len(persisted) == 3
        codes = {r.req_code for r in persisted}
        assert codes == {"REQ-01", "REQ-02", "REQ-03"}

        # Verify keywords are arrays
        for r in persisted:
            assert isinstance(r.keywords, list)
            assert len(r.keywords) > 0

    finally:
        db.rollback()
        db.close()


def test_extract_requirements_total_failure_fallback():
    """Both LLM attempts fail → falls back to single REQ-01 covering whole query."""
    db = SessionLocal()
    try:
        query = _create_query(db, MICRO_QUERY)

        with patch(
            "app.generation.requirement_extraction.call_with_retry_and_fallback",
            side_effect=LLMCallError("All attempts failed"),
        ):
            reqs = extract_requirements(db, query.id, MICRO_QUERY)
            db.commit()

        # Should produce exactly one fallback requirement
        assert len(reqs) == 1
        assert reqs[0].req_code == "REQ-01"
        assert reqs[0].description == MICRO_QUERY

        # Verify persistence
        persisted = db.query(RequirementModel).filter(
            RequirementModel.query_id == query.id
        ).all()
        assert len(persisted) == 1
        assert persisted[0].req_code == "REQ-01"
        assert persisted[0].description == MICRO_QUERY

    finally:
        db.rollback()
        db.close()

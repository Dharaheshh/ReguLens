"""Tests for Citation Validator — TASK-013.

Fully deterministic tests — no LLM call, no mocking needed.
Tests cover:
1. All proposed codes valid → one citation row per code
2. Mixed valid/invalid codes → only valid ones get citation rows
3. All codes invalid → zero citations AND validation_state = 'UNSUPPORTED'
"""
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db import SessionLocal
from app.models import (
    RegulatoryQuery, Response, Claim, Citation, Evidence, Document,
    DocumentVersion, Chunk,
)
from app.validation.citation_validator import validate_citations


FIXTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
SAMPLE_PDF = os.path.join(FIXTURE_DIR, "sample_3page.pdf")


def _setup_evidence(db) -> tuple[uuid.UUID, list[str]]:
    """Ingest the fixture PDF and return (document_id, list of evidence_codes).

    Uses the API to ingest, so chunks and evidence rows are created properly.
    """
    client = TestClient(app)
    with open(SAMPLE_PDF, "rb") as f:
        resp = client.post(
            "/api/v1/documents",
            files={"file": ("sample_3page.pdf", f, "application/pdf")},
            data={"doc_type": "scientific_paper", "is_synthetic": "true"},
        )
    assert resp.status_code == 201
    doc_id = uuid.UUID(resp.json()["document_id"])

    evidence_rows = db.query(Evidence).filter(Evidence.document_id == doc_id).all()
    codes = [e.evidence_code for e in evidence_rows]
    return doc_id, codes


def _create_claim(db) -> Claim:
    """Helper to create a regulatory_query → response → claim chain."""
    query = RegulatoryQuery(query_text="Test query")
    db.add(query)
    db.flush()

    response = Response(query_id=query.id, draft_text="Test draft", status="draft")
    db.add(response)
    db.flush()

    claim = Claim(
        response_id=response.id,
        claim_code="CLM-TEST",
        claim_text="Test claim text",
        product_topic="test_topic",
    )
    db.add(claim)
    db.flush()
    return claim


def test_all_codes_valid():
    """All proposed evidence codes are valid → one citation row per code."""
    db = SessionLocal()
    try:
        doc_id, evidence_codes = _setup_evidence(db)
        assert len(evidence_codes) > 0, "Need evidence to test with"

        claim = _create_claim(db)

        # Use the first two evidence codes (or all if fewer)
        codes_to_validate = evidence_codes[:2]

        validate_citations(db, claim.id, codes_to_validate)
        db.commit()

        citations = db.query(Citation).filter(Citation.claim_id == claim.id).all()
        assert len(citations) == len(codes_to_validate)

        for c in citations:
            assert c.validated is True

        # validation_state should NOT be UNSUPPORTED
        refreshed_claim = db.query(Claim).filter(Claim.id == claim.id).first()
        assert refreshed_claim.validation_state != "UNSUPPORTED"

    finally:
        db.rollback()
        db.close()


def test_mixed_valid_invalid_codes():
    """Mixed valid and invalid codes → only valid ones get citation rows."""
    db = SessionLocal()
    try:
        doc_id, evidence_codes = _setup_evidence(db)
        assert len(evidence_codes) > 0

        claim = _create_claim(db)

        # Mix: one real code + two fake codes
        mixed_codes = [evidence_codes[0], "EVD-99999", "EVD-FAKE1"]

        validate_citations(db, claim.id, mixed_codes)
        db.commit()

        citations = db.query(Citation).filter(Citation.claim_id == claim.id).all()
        assert len(citations) == 1  # Only the valid one

        # The valid citation should be for the first evidence code
        evidence_row = db.query(Evidence).filter(
            Evidence.evidence_code == evidence_codes[0]
        ).first()
        assert citations[0].evidence_id == evidence_row.id
        assert citations[0].validated is True

    finally:
        db.rollback()
        db.close()


def test_all_codes_invalid_sets_unsupported():
    """All codes invalid → zero citation rows AND validation_state = 'UNSUPPORTED'."""
    db = SessionLocal()
    try:
        claim = _create_claim(db)

        fake_codes = ["EVD-FAKE1", "EVD-FAKE2", "EVD-NONEXIST"]

        validate_citations(db, claim.id, fake_codes)
        db.commit()

        # Zero citations
        citations = db.query(Citation).filter(Citation.claim_id == claim.id).all()
        assert len(citations) == 0

        # validation_state should be UNSUPPORTED
        refreshed_claim = db.query(Claim).filter(Claim.id == claim.id).first()
        assert refreshed_claim.validation_state == "UNSUPPORTED"

    finally:
        db.rollback()
        db.close()

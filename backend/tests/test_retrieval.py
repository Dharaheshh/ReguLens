"""Tests for TASK-009 - Hybrid Retrieval with RRF fusion."""
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app.retrieval.fusion import reciprocal_rank_fusion, RankedItem, FusedResult


# ── Unit test: RRF math against known fixture ──

def test_rrf_math_known_fixture():
    """Test RRF fusion with hand-constructed ranked lists.

    Setup:
        Lexical: [A, B, C]  (ranks 1, 2, 3)
        Vector:  [B, D, A]  (ranks 1, 2, 3)

    Expected RRF scores (k=60):
        A: 1/(60+1) + 1/(60+3) = 1/61 + 1/63 ≈ 0.016393 + 0.015873 = 0.032267
        B: 1/(60+2) + 1/(60+1) = 1/62 + 1/61 ≈ 0.016129 + 0.016393 = 0.032522
        C: 1/(60+3) = 1/63 ≈ 0.015873
        D: 1/(60+2) = 1/62 ≈ 0.016129

    Expected order: B > A > D > C
    """
    id_a = uuid.uuid4()
    id_b = uuid.uuid4()
    id_c = uuid.uuid4()
    id_d = uuid.uuid4()

    lexical = [
        RankedItem(chunk_id=id_a, content="A"),
        RankedItem(chunk_id=id_b, content="B"),
        RankedItem(chunk_id=id_c, content="C"),
    ]
    vector = [
        RankedItem(chunk_id=id_b, content="B"),
        RankedItem(chunk_id=id_d, content="D"),
        RankedItem(chunk_id=id_a, content="A"),
    ]

    results = reciprocal_rank_fusion(lexical, vector, k=4)

    assert len(results) == 4
    assert results[0].chunk_id == id_b  # B appears in both at high ranks
    assert results[1].chunk_id == id_a  # A appears in both
    assert results[2].chunk_id == id_d  # D appears in vector only at rank 2
    assert results[3].chunk_id == id_c  # C appears in lexical only at rank 3

    # Verify exact scores
    score_b = 1 / (60 + 2) + 1 / (60 + 1)  # lex rank 2, vec rank 1
    score_a = 1 / (60 + 1) + 1 / (60 + 3)  # lex rank 1, vec rank 3
    score_d = 1 / (60 + 2)                   # vec rank 2 only
    score_c = 1 / (60 + 3)                   # lex rank 3 only

    assert abs(results[0].score - score_b) < 1e-10
    assert abs(results[1].score - score_a) < 1e-10
    assert abs(results[2].score - score_d) < 1e-10
    assert abs(results[3].score - score_c) < 1e-10


def test_rrf_respects_k_limit():
    """RRF returns at most k results."""
    items = [
        RankedItem(chunk_id=uuid.uuid4(), content=f"item-{i}")
        for i in range(10)
    ]
    results = reciprocal_rank_fusion(items, [], k=3)
    assert len(results) == 3


def test_rrf_deduplicates_across_lists():
    """A chunk appearing in both lists gets a single fused entry, not two."""
    shared_id = uuid.uuid4()
    lexical = [RankedItem(chunk_id=shared_id, content="shared")]
    vector = [RankedItem(chunk_id=shared_id, content="shared")]

    results = reciprocal_rank_fusion(lexical, vector, k=5)
    assert len(results) == 1
    # Score should be sum of both rank contributions
    expected = 1 / (60 + 1) + 1 / (60 + 1)
    assert abs(results[0].score - expected) < 1e-10


# ── Integration test: ingest fixture PDF, then search ──

def test_hybrid_search_returns_relevant_chunk():
    """Ingest sample_3page.pdf, run hybrid_search, check relevant chunk in top-5."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.db import SessionLocal
    from app.retrieval.hybrid_search import hybrid_search

    client = TestClient(app)

    fixture_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "fixtures", "sample_3page.pdf"
    )

    # Ingest the fixture PDF via the API
    with open(fixture_path, "rb") as f:
        resp = client.post(
            "/api/v1/documents",
            files={"file": ("sample_3page.pdf", f, "application/pdf")},
            data={"doc_type": "scientific_paper", "is_synthetic": "true"},
        )
    assert resp.status_code == 201

    # Search for content we know is in the fixture
    db = SessionLocal()
    try:
        results = hybrid_search(db, "microbiological safety pathogen screening", k=5)

        assert len(results) > 0, "Expected at least one search result"

        # The fixture contains "microbiological safety" on page 1 and
        # "pathogen screening" on page 2 — at least one chunk should match
        all_content = " ".join(r.content for r in results)
        assert (
            "microbiological" in all_content.lower()
            or "pathogen" in all_content.lower()
        ), f"Expected relevant content in results, got: {all_content[:200]}"

        # Verify SearchResult structure
        for r in results:
            assert r.chunk_id is not None
            assert r.content is not None
            assert r.score > 0
    finally:
        db.close()

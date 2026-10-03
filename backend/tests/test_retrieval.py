"""Tests for TASK-009 - Hybrid Retrieval with RRF fusion.

Phase 1 additions:
- test_hybrid_search_irrelevant_query_returns_empty: verifies the relevance
  floor drops garbage results for queries with no semantic/lexical relationship.
- test_hybrid_search_never_exceeds_k: confirms hard top-k cap.
"""
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
    import time
    try:
        start_time = time.time()
        results = hybrid_search(db, "microbiological safety pathogen screening", k=5)
        latency = time.time() - start_time
        print(f"\n--- HYBRID SEARCH PIPELINE LATENCY: {latency:.4f} seconds ---")

        assert len(results) > 0, "Expected at least one search result"
        assert len(results) <= 5, f"Expected at most 5 results, got {len(results)}"

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


# ── Phase 1: Relevance floor tests ──

def test_hybrid_search_irrelevant_query_returns_empty():
    """A query with no semantic/lexical relationship to the ingested corpus
    should return an EMPTY list, not a low-quality top-5 of garbage results.

    This verifies the RETRIEVAL_MIN_SCORE relevance floor works.
    """
    from fastapi.testclient import TestClient
    from app.main import app
    from app.db import SessionLocal
    from app.retrieval.hybrid_search import hybrid_search

    client = TestClient(app)

    # Ensure there is data in the DB (re-ingest fixture if needed)
    fixture_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "fixtures", "sample_3page.pdf"
    )
    with open(fixture_path, "rb") as f:
        resp = client.post(
            "/api/v1/documents",
            files={"file": ("sample_3page.pdf", f, "application/pdf")},
            data={"doc_type": "scientific_paper", "is_synthetic": "true"},
        )
    # 201 = new, or might already exist — either is fine

    db = SessionLocal()
    try:
        # "hi" has no semantic or lexical relationship to a regulatory dossier
        results = hybrid_search(db, "hi")
        assert results == [], (
            f"Expected empty results for irrelevant query 'hi', "
            f"got {len(results)} results with scores: "
            f"{[r.score for r in results]}"
        )

        # Another test with a totally unrelated query
        results2 = hybrid_search(db, "what's the weather today in Paris")
        assert results2 == [], (
            f"Expected empty results for unrelated query, "
            f"got {len(results2)} results with scores: "
            f"{[r.score for r in results2]}"
        )
    finally:
        db.close()


def test_hybrid_search_never_exceeds_k():
    """hybrid_search must never return more than k results, regardless of how
    many candidates fusion produces."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.db import SessionLocal
    from app.retrieval.hybrid_search import hybrid_search

    client = TestClient(app)

    fixture_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "fixtures", "sample_3page.pdf"
    )
    with open(fixture_path, "rb") as f:
        client.post(
            "/api/v1/documents",
            files={"file": ("sample_3page.pdf", f, "application/pdf")},
            data={"doc_type": "scientific_paper", "is_synthetic": "true"},
        )

    db = SessionLocal()
    try:
        # With k=2, should never get more than 2
        results = hybrid_search(db, "microbiological safety pathogen", k=2)
        assert len(results) <= 2, f"Expected at most 2 results, got {len(results)}"

        # With k=1, should never get more than 1
        results1 = hybrid_search(db, "microbiological safety pathogen", k=1)
        assert len(results1) <= 1, f"Expected at most 1 result, got {len(results1)}"
    finally:
        db.close()

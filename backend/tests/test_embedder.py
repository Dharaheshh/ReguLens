"""Tests for TASK-007 - Embeddings + evidence storage."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app.ingestion.embedder import embed, embed_batch


def test_embed_returns_384_dimensions():
    """embed() returns a list of 384 floats."""
    result = embed("This is a test sentence about microbiological safety.")
    assert isinstance(result, list)
    assert len(result) == 384
    assert all(isinstance(x, float) for x in result)


def test_embed_batch():
    """embed_batch() returns correct number of embeddings."""
    texts = ["First text.", "Second text.", "Third text."]
    results = embed_batch(texts)
    assert len(results) == 3
    for r in results:
        assert len(r) == 384


def test_embed_normalized():
    """Embeddings are normalized (unit length)."""
    import math
    result = embed("Test normalization.")
    magnitude = math.sqrt(sum(x * x for x in result))
    assert abs(magnitude - 1.0) < 0.01

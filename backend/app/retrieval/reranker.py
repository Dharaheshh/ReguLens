"""Reranker - TASK-014 Phase 3.

Implements cross-encoder reranking over the fused candidate set.
"""
import logging
from typing import Optional
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)

_model: Optional[CrossEncoder] = None


import torch

def _get_model() -> CrossEncoder:
    """Lazy-load the cross-encoder model."""
    global _model
    if _model is None:
        logger.info("Loading cross-encoder model...")
        _model = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2", 
            max_length=512,
            activation_fn=torch.nn.Sigmoid()
        )
    return _model


def rerank(query: str, chunks: list[str]) -> list[float]:
    """Score a list of chunks against a query using the cross-encoder.

    Args:
        query: The search query string.
        chunks: List of chunk text strings.

    Returns:
        List of float scores corresponding to the chunks. Higher is better.
        Returns empty list if chunks is empty.
    """
    if not chunks:
        return []

    try:
        model = _get_model()
        pairs = [[query, chunk] for chunk in chunks]
        scores = model.predict(pairs)
        
        # sentence-transformers predict returns a numpy array, convert to list of floats
        return [float(score) for score in scores]
        
    except Exception as e:
        logger.warning(f"Reranker failed, falling back to original order. Error: {e}")
        # Return fallback scores that preserve the original order (descending)
        # We just return artificial scores from 1.0 down to 0.0 based on index
        # This will be handled gracefully by the caller if they check for failures,
        # but to be safe we raise so the caller can explicitly fall back to RRF.
        raise

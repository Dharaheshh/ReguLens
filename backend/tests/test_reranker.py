"""Tests for TASK-014 Phase 3 - Reranker."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.retrieval.reranker import rerank

def test_reranker_reorders_misleading_fusion():
    """Given a known fixture set where fusion might produce a less optimal
    order, confirm reranker fixes it.
    """
    query = "microbiological safety pathogen screening"
    
    # Candidate 0 is completely irrelevant text about something else
    # Candidate 1 is highly relevant
    chunks = [
        "The project budget was approved in Q3 for the marketing team. " * 5,
        "We performed extensive pathogen screening on all samples, ensuring "
        "strict microbiological safety standards were met."
    ]
    
    scores = rerank(query, chunks)
    
    assert len(scores) == 2
    # The relevant chunk (index 1) should score higher than the irrelevant one (index 0)
    assert scores[1] > scores[0], f"Expected relevant chunk to score higher, got {scores}"

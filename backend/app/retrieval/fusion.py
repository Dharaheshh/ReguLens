"""Reciprocal Rank Fusion - TASK-009.

Combines two ranked lists using RRF as specified in AI_RAG_DESIGN.md:
    score = sum(1 / (60 + rank)) across whichever list(s) a chunk appears in.
"""
from dataclasses import dataclass
import uuid


@dataclass
class RankedItem:
    chunk_id: uuid.UUID
    content: str
    evidence_id: uuid.UUID | None = None
    evidence_code: str | None = None
    source_type: str | None = None


@dataclass
class FusedResult:
    chunk_id: uuid.UUID
    content: str
    score: float
    evidence_id: uuid.UUID | None = None
    evidence_code: str | None = None
    source_type: str | None = None


def reciprocal_rank_fusion(
    lexical_results: list[RankedItem],
    vector_results: list[RankedItem],
    k: int = 5,
    rrf_k: int = 60,
) -> list[FusedResult]:
    """Fuse two ranked result lists using Reciprocal Rank Fusion.

    For each chunk, score = sum(1 / (rrf_k + rank)) across whichever list(s)
    it appears in. Rank is 1-based.

    Args:
        lexical_results: Ranked list from lexical (tsvector) search.
        vector_results: Ranked list from vector (HNSW) search.
        k: Number of top results to return.
        rrf_k: RRF constant (default 60, per AI_RAG_DESIGN.md).

    Returns:
        Top-k results sorted by fused score (descending).
    """
    scores: dict[uuid.UUID, float] = {}
    item_map: dict[uuid.UUID, RankedItem] = {}

    for rank, item in enumerate(lexical_results, start=1):
        scores[item.chunk_id] = scores.get(item.chunk_id, 0.0) + 1.0 / (rrf_k + rank)
        item_map[item.chunk_id] = item

    for rank, item in enumerate(vector_results, start=1):
        scores[item.chunk_id] = scores.get(item.chunk_id, 0.0) + 1.0 / (rrf_k + rank)
        if item.chunk_id not in item_map:
            item_map[item.chunk_id] = item

    fused = [
        FusedResult(
            chunk_id=cid,
            content=item_map[cid].content,
            score=score,
            evidence_id=item_map[cid].evidence_id,
            evidence_code=item_map[cid].evidence_code,
            source_type=item_map[cid].source_type,
        )
        for cid, score in scores.items()
    ]

    fused.sort(key=lambda x: x.score, reverse=True)
    return fused[:k]

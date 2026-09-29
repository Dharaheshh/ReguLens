"""Reciprocal Rank Fusion - TASK-009."""
from dataclasses import dataclass
from typing import Sequence, TypeVar, Hashable

T = TypeVar('T', bound=Hashable)

@dataclass
class FusedResult:
    item: T
    score: float

def reciprocal_rank_fusion(
    lists: list[Sequence[T]],
    k: int = 60
) -> list[FusedResult]:
    """Combine ranked lists using RRF.

    score = sum(1 / (k + rank)) across all lists where the item appears.
    Rank is 1-indexed.
    """
    scores: dict[T, float] = {}
    for result_list in lists:
        for rank, item in enumerate(result_list, start=1):
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + rank)
            
    # Sort by score descending
    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [FusedResult(item=item, score=score) for item, score in sorted_items]

"""Hybrid search - TASK-009.

Implements lexical + vector search with RRF fusion per AI_RAG_DESIGN.md.
After fusion, a minimum-relevance floor (RETRIEVAL_MIN_SCORE) is enforced:
results below this floor are dropped even if they would otherwise be in the
top-k.  A requirement can legitimately return fewer than k results, or zero
results, when nothing meets the floor — this is correct behaviour, not a bug.
"""
import logging
import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import text as sa_text

from app.ingestion.embedder import embed
from app.models import Chunk, Evidence
from app.retrieval.fusion import RankedItem, FusedResult, reciprocal_rank_fusion
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    chunk_id: uuid.UUID
    evidence_id: uuid.UUID | None
    evidence_code: str | None
    content: str
    score: float
    source_type: str | None = None


def _lexical_search(db: Session, query_text: str, limit: int = 20) -> list[RankedItem]:
    """Lexical search using tsvector/GIN index."""
    sql = sa_text("""
        SELECT c.id, c.content, e.id AS evidence_id, e.evidence_code, e.source_type
        FROM chunks c
        LEFT JOIN evidence e ON e.chunk_id = c.id
        WHERE c.tsv @@ plainto_tsquery('english', :q)
        ORDER BY ts_rank(c.tsv, plainto_tsquery('english', :q)) DESC
        LIMIT :limit
    """)
    rows = db.execute(sql, {"q": query_text, "limit": limit}).fetchall()
    return [
        RankedItem(
            chunk_id=row[0],
            content=row[1],
            evidence_id=row[2],
            evidence_code=row[3],
            source_type=row[4],
        )
        for row in rows
    ]


def _vector_search(db: Session, query_embedding: list[float], limit: int = 20) -> list[RankedItem]:
    """Vector search using HNSW cosine distance index."""
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
    sql = sa_text("""
        SELECT c.id, c.content, e.id AS evidence_id, e.evidence_code, e.source_type
        FROM chunks c
        LEFT JOIN evidence e ON e.chunk_id = c.id
        ORDER BY c.embedding <=> :emb ::vector
        LIMIT :limit
    """)
    rows = db.execute(sql, {"emb": embedding_str, "limit": limit}).fetchall()
    return [
        RankedItem(
            chunk_id=row[0],
            content=row[1],
            evidence_id=row[2],
            evidence_code=row[3],
            source_type=row[4],
        )
        for row in rows
    ]


def hybrid_search(db: Session, query_text: str, k: int | None = None) -> list[SearchResult]:
    """Run hybrid retrieval: lexical + vector search with RRF fusion, then rerank.

    After RRF fusion, the top-20 candidates are passed to a cross-encoder reranker.
    The reranked list is hard-capped to top-k (default from settings.RETRIEVAL_TOP_K)
    and then filtered by the minimum relevance floor (settings.RERANK_MIN_SCORE).
    Results below the floor are dropped.

    If the reranker fails, it falls back to the RRF-fused order and the
    RETRIEVAL_MIN_SCORE floor.

    Args:
        db: SQLAlchemy session.
        query_text: The search query string.
        k: Number of top results to return.  Defaults to settings.RETRIEVAL_TOP_K.

    Returns:
        Top-k SearchResult objects sorted by reranker score, filtered by floor.
    """
    if k is None:
        k = settings.RETRIEVAL_TOP_K

    query_embedding = embed(query_text)

    lexical_results = _lexical_search(db, query_text, limit=20)
    vector_results = _vector_search(db, query_embedding, limit=20)

    logger.info(
        "Lexical: %d results, Vector: %d results",
        len(lexical_results),
        len(vector_results),
    )

    # Fuse with RRF — request a wider candidate set (20) for the reranker
    fused = reciprocal_rank_fusion(lexical_results, vector_results, k=20)
    
    if not fused:
        return []

    # Apply Reranker
    try:
        from app.retrieval.reranker import rerank
        chunks_text = [r.content for r in fused]
        rerank_scores = rerank(query_text, chunks_text)
        
        # Update fused results with reranker scores
        for r, score in zip(fused, rerank_scores):
            r.score = score
            
        # Sort by reranker score descending
        fused.sort(key=lambda x: x.score, reverse=True)
        
        min_score = settings.RERANK_MIN_SCORE
        logger.info("Using reranker scores. Applied floor: %.4f", min_score)
        
    except Exception as e:
        logger.warning("Reranker failed (%s), falling back to RRF scores.", e)
        # RRF order is already intact, just apply the RRF-specific floor
        min_score = settings.RETRIEVAL_MIN_SCORE
        logger.info("Using fallback RRF scores. Applied floor: %.4f", min_score)

    # Hard cap to top-k
    fused = fused[:k]

    # Apply minimum relevance floor (either RERANK_MIN_SCORE or RETRIEVAL_MIN_SCORE depending on what ran)
    filtered = [r for r in fused if r.score >= min_score]

    if len(filtered) < len(fused):
        logger.info(
            "Relevance floor (%.4f) dropped %d of %d top-k results",
            min_score,
            len(fused) - len(filtered),
            len(fused),
        )

    if not filtered:
        logger.info("No results above the relevance floor for query: %s", query_text[:80])

    return [
        SearchResult(
            chunk_id=r.chunk_id,
            evidence_id=r.evidence_id,
            evidence_code=r.evidence_code,
            content=r.content,
            score=r.score,
            source_type=r.source_type,
        )
        for r in filtered
    ]


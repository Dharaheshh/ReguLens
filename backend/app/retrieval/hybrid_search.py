"""Hybrid search - TASK-009.

Implements lexical + vector search with RRF fusion per AI_RAG_DESIGN.md.
"""
import logging
import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import text as sa_text

from app.ingestion.embedder import embed
from app.models import Chunk, Evidence
from app.retrieval.fusion import RankedItem, FusedResult, reciprocal_rank_fusion

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    chunk_id: uuid.UUID
    evidence_id: uuid.UUID | None
    evidence_code: str | None
    content: str
    score: float


def _lexical_search(db: Session, query_text: str, limit: int = 20) -> list[RankedItem]:
    """Lexical search using tsvector/GIN index.

    SELECT chunks.id, chunks.content, evidence.id, evidence.evidence_code, evidence.source_type
    FROM chunks
    LEFT JOIN evidence ON evidence.chunk_id = chunks.id
    WHERE chunks.tsv @@ plainto_tsquery('english', :q)
    ORDER BY ts_rank(chunks.tsv, plainto_tsquery('english', :q)) DESC
    LIMIT :limit
    """
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
    """Vector search using HNSW cosine distance index.

    SELECT chunks.id, chunks.content, evidence.id, evidence.evidence_code, evidence.source_type
    FROM chunks
    LEFT JOIN evidence ON evidence.chunk_id = chunks.id
    ORDER BY chunks.embedding <=> :query_embedding
    LIMIT :limit
    """
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


def hybrid_search(db: Session, query_text: str, k: int = 5) -> list[SearchResult]:
    """Run hybrid retrieval: lexical + vector search with RRF fusion.

    Args:
        db: SQLAlchemy session.
        query_text: The search query string.
        k: Number of top results to return (default 5).

    Returns:
        Top-k SearchResult objects sorted by fused RRF score.
    """
    # Generate query embedding using the same embedder as ingestion
    query_embedding = embed(query_text)

    # Run both searches
    lexical_results = _lexical_search(db, query_text, limit=20)
    vector_results = _vector_search(db, query_embedding, limit=20)

    logger.info(
        "Lexical: %d results, Vector: %d results",
        len(lexical_results),
        len(vector_results),
    )

    # Fuse with RRF
    fused = reciprocal_rank_fusion(lexical_results, vector_results, k=k)

    return [
        SearchResult(
            chunk_id=r.chunk_id,
            evidence_id=r.evidence_id,
            evidence_code=r.evidence_code,
            content=r.content,
            score=r.score,
        )
        for r in fused
    ]

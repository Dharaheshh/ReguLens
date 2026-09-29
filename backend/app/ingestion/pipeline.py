"""Ingestion pipeline - TASK-007/008.

Orchestrates: parse -> chunk -> embed -> store (chunks + evidence).
All-or-nothing: either fully ingested or rolled back.
"""
import logging
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.ingestion.parser import parse_pdf, ParsedPage, UnsupportedDocumentError
from app.ingestion.chunker import chunk, ChunkData
from app.ingestion.embedder import embed_batch
from app.models import Chunk, Evidence, Document, DocumentVersion

logger = logging.getLogger(__name__)


def run_ingestion(
    db: Session,
    file_path: str,
    document_id: uuid.UUID,
    document_version_id: uuid.UUID,
    source_type: str,
) -> int:
    """Run the full ingestion pipeline for a document version.

    Steps:
    1. Parse PDF -> pages
    2. Chunk pages -> chunks
    3. Embed all chunks (batch)
    4. Store chunks + evidence rows in a single transaction

    Args:
        db: SQLAlchemy session (caller manages commit/rollback)
        file_path: Path to the PDF file
        document_id: UUID of the parent document
        document_version_id: UUID of the document version
        source_type: doc_type of the document

    Returns:
        Number of chunks created.

    Raises:
        UnsupportedDocumentError: If PDF cannot be parsed.
        Exception: On embedding or storage failure.
    """
    # Step 1: Parse
    pages: list[ParsedPage] = parse_pdf(file_path)
    logger.info("Parsed %d pages from %s", len(pages), file_path)

    # Step 2: Chunk
    chunk_data_list: list[ChunkData] = chunk(pages)
    if not chunk_data_list:
        logger.warning("No chunks produced from %s", file_path)
        return 0
    logger.info("Produced %d chunks", len(chunk_data_list))

    # Step 3: Embed (batch for efficiency)
    texts = [c.content for c in chunk_data_list]
    embeddings = embed_batch(texts)
    logger.info("Generated %d embeddings", len(embeddings))

    # Step 4: Store — all or nothing within caller's transaction
    for chunk_data, embedding in zip(chunk_data_list, embeddings):
        chunk_row = Chunk(
            document_version_id=document_version_id,
            section=chunk_data.section,
            page_start=chunk_data.page_start,
            page_end=chunk_data.page_end,
            content=chunk_data.content,
            embedding=embedding,
        )
        db.add(chunk_row)
        db.flush()  # get the chunk ID

        seq_val = db.execute(text("SELECT nextval('evidence_code_seq')")).scalar()
        evidence_code = f"EVD-{seq_val:05d}"
        
        evidence_row = Evidence(
            evidence_code=evidence_code,
            chunk_id=chunk_row.id,
            document_id=document_id,
            document_version_id=document_version_id,
            source_type=source_type,
        )
        db.add(evidence_row)

    logger.info("Stored %d chunks and evidence rows", len(chunk_data_list))
    return len(chunk_data_list)

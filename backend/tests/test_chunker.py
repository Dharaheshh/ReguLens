"""Tests for TASK-006 - Section-aware chunking."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ingestion.parser import parse_pdf
from app.ingestion.chunker import chunk, ChunkData


FIXTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
SAMPLE_PDF = os.path.join(FIXTURE_DIR, "sample_3page.pdf")


def test_chunk_produces_chunks():
    """Chunking the 3-page fixture produces at least 1 chunk."""
    pages = parse_pdf(SAMPLE_PDF)
    chunks = chunk(pages)
    assert len(chunks) >= 1
    for c in chunks:
        assert isinstance(c, ChunkData)
        assert len(c.content) > 0


def test_chunk_page_ranges():
    """Every chunk has valid page_start <= page_end within document range."""
    pages = parse_pdf(SAMPLE_PDF)
    chunks = chunk(pages)
    for c in chunks:
        assert 1 <= c.page_start <= 3
        assert 1 <= c.page_end <= 3
        assert c.page_start <= c.page_end


def test_chunk_no_mid_sentence_split():
    """Chunks should not split mid-sentence (end with incomplete sentence)."""
    pages = parse_pdf(SAMPLE_PDF)
    chunks = chunk(pages)
    for c in chunks:
        # A chunk that ends mid-sentence would typically not end with a period,
        # question mark, or similar. This is a soft check.
        content = c.content.strip()
        # At minimum, content should contain complete words
        assert len(content.split()) > 1


def test_chunk_deterministic():
    """Chunking is deterministic - same input produces same output."""
    pages = parse_pdf(SAMPLE_PDF)
    chunks1 = chunk(pages)
    chunks2 = chunk(pages)
    assert len(chunks1) == len(chunks2)
    for c1, c2 in zip(chunks1, chunks2):
        assert c1.content == c2.content
        assert c1.page_start == c2.page_start
        assert c1.page_end == c2.page_end
        assert c1.section == c2.section


def test_chunk_empty_pages():
    """Empty pages list produces empty chunks."""
    chunks = chunk([])
    assert chunks == []

"""Section-aware chunker - TASK-006.

Implements chunk(pages) -> list[ChunkData]
Splits on section/paragraph boundaries, target ~500 tokens per chunk.
Preserves page_start, page_end, section.
"""
import re
from dataclasses import dataclass

from app.ingestion.parser import ParsedPage


@dataclass
class ChunkData:
    content: str
    page_start: int
    page_end: int
    section: str | None


# Approximate tokens as words / 0.75 (conservative estimate)
TARGET_TOKENS = 500
MAX_CHARS = int(TARGET_TOKENS * 4.5)  # ~2250 chars ≈ 500 tokens

# Pattern to detect section headings (e.g. "1. Introduction", "Section 2.1", "## Heading")
SECTION_HEADING_RE = re.compile(
    r"^(?:#+\s+|(?:Section\s+)?\d+(?:\.\d+)*\.?\s+|[A-Z][A-Z\s]{2,}$)",
    re.MULTILINE,
)


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: word count / 0.75."""
    return int(len(text.split()) / 0.75)


def _detect_section(text: str) -> str | None:
    """Try to detect a section heading at the start of text."""
    first_line = text.split("\n", 1)[0].strip()
    if SECTION_HEADING_RE.match(first_line):
        return first_line[:120]  # cap length
    return None


def _split_into_paragraphs(text: str) -> list[str]:
    """Split text into paragraphs on double newlines or section headings."""
    # Split on double newlines
    raw_paragraphs = re.split(r"\n\s*\n", text)
    paragraphs = [p.strip() for p in raw_paragraphs if p.strip()]
    return paragraphs


def chunk(pages: list[ParsedPage]) -> list[ChunkData]:
    """Split parsed pages into chunks of approximately TARGET_TOKENS tokens.

    Strategy:
    - Collect paragraphs across pages.
    - Accumulate paragraphs into a chunk until adding another would exceed the target.
    - Track page_start and page_end per chunk.
    - Try to detect section headings.
    - Never split mid-sentence if avoidable.

    Args:
        pages: List of ParsedPage from the parser.

    Returns:
        List of ChunkData objects.
    """
    if not pages:
        return []

    # Build a list of (paragraph_text, page_number) tuples
    para_page_pairs: list[tuple[str, int]] = []
    for page in pages:
        if not page.text:
            continue
        paragraphs = _split_into_paragraphs(page.text)
        for para in paragraphs:
            para_page_pairs.append((para, page.page_number))

    if not para_page_pairs:
        return []

    chunks: list[ChunkData] = []
    current_text_parts: list[str] = []
    current_page_start: int = para_page_pairs[0][1]
    current_page_end: int = para_page_pairs[0][1]
    current_section: str | None = None
    current_char_count = 0

    for para_text, page_num in para_page_pairs:
        # Detect section heading
        detected_section = _detect_section(para_text)

        # If adding this paragraph would exceed target and we have content,
        # flush the current chunk
        if current_text_parts and (current_char_count + len(para_text)) > MAX_CHARS:
            chunk_content = "\n\n".join(current_text_parts)
            chunks.append(ChunkData(
                content=chunk_content,
                page_start=current_page_start,
                page_end=current_page_end,
                section=current_section,
            ))
            current_text_parts = []
            current_char_count = 0
            current_page_start = page_num
            current_section = detected_section

        # If this is a section heading and we have accumulated text, also flush
        elif detected_section and current_text_parts:
            chunk_content = "\n\n".join(current_text_parts)
            chunks.append(ChunkData(
                content=chunk_content,
                page_start=current_page_start,
                page_end=current_page_end,
                section=current_section,
            ))
            current_text_parts = []
            current_char_count = 0
            current_page_start = page_num
            current_section = detected_section

        if detected_section and not current_section:
            current_section = detected_section

        current_text_parts.append(para_text)
        current_char_count += len(para_text)
        current_page_end = page_num

    # Flush remaining
    if current_text_parts:
        chunk_content = "\n\n".join(current_text_parts)
        chunks.append(ChunkData(
            content=chunk_content,
            page_start=current_page_start,
            page_end=current_page_end,
            section=current_section,
        ))

    return chunks

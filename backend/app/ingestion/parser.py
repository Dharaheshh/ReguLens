"""PDF parser - TASK-005.

Implements parse_pdf(file_path) -> list[ParsedPage]
Rejects scanned/image-only PDFs with UNSUPPORTED_DOCUMENT error.
"""
import os
from dataclasses import dataclass

import pymupdf  # PyMuPDF


@dataclass
class ParsedPage:
    page_number: int
    text: str


class UnsupportedDocumentError(Exception):
    """Raised when a PDF cannot be parsed (scanned/image-only)."""
    pass


def parse_pdf(file_path: str) -> list[ParsedPage]:
    """Parse a text-based PDF and return a list of ParsedPage objects.

    Args:
        file_path: Absolute path to the PDF file.

    Returns:
        List of ParsedPage with page_number (1-based) and extracted text.

    Raises:
        FileNotFoundError: If the file does not exist.
        UnsupportedDocumentError: If the PDF is scanned/image-only or contains no extractable text.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if not file_path.lower().endswith(".pdf"):
        raise ValueError(f"Not a PDF file: {file_path}")

    doc = pymupdf.open(file_path)
    pages: list[ParsedPage] = []
    total_text_length = 0

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        text = page.get_text("text").strip()
        pages.append(ParsedPage(page_number=page_idx + 1, text=text))
        total_text_length += len(text)

    doc.close()

    if total_text_length == 0:
        raise UnsupportedDocumentError(
            "UNSUPPORTED_DOCUMENT: PDF contains no extractable text. "
            "Scanned/image-only PDFs are not supported."
        )

    return pages

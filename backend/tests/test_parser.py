"""Tests for TASK-005 - PDF parsing."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app.ingestion.parser import parse_pdf, ParsedPage, UnsupportedDocumentError


FIXTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
SAMPLE_PDF = os.path.join(FIXTURE_DIR, "sample_3page.pdf")


def test_parse_pdf_returns_3_pages():
    """Given the 3-page fixture, returns 3 ParsedPage objects with correct page numbers."""
    pages = parse_pdf(SAMPLE_PDF)
    assert len(pages) == 3
    for i, page in enumerate(pages):
        assert isinstance(page, ParsedPage)
        assert page.page_number == i + 1
        assert len(page.text) > 0


def test_parse_pdf_page_content():
    """Verify each page contains expected content."""
    pages = parse_pdf(SAMPLE_PDF)
    assert "Introduction" in pages[0].text
    assert "Methodology" in pages[1].text or "Pathogen" in pages[1].text
    assert "Results" in pages[2].text


def test_parse_pdf_file_not_found():
    """Raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        parse_pdf("/nonexistent/path/file.pdf")


def test_parse_pdf_not_a_pdf():
    """Raises ValueError for non-PDF file."""
    with pytest.raises(ValueError):
        parse_pdf(__file__)  # This .py file is not a PDF

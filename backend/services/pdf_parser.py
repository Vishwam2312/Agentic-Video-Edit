"""
services/pdf_parser.py
───────────────────────
PDF text extraction using PyMuPDF (imported as `fitz`).

Responsibilities:
  - Open a PDF from a file-system path.
  - Extract all text page-by-page.
  - Read document-level metadata (title, author, subject, producer).
  - Return a structured ParseResult dataclass — no I/O side-effects,
    so it is easy to test in isolation.

The result is persisted to MongoDB by the caller (upload router).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF
from loguru import logger


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class ParseResult:
    """All information extracted from a single PDF."""

    text: str
    text_length: int
    word_count: int
    page_count: int
    pdf_title: Optional[str] = None
    pdf_author: Optional[str] = None
    pdf_subject: Optional[str] = None
    pdf_producer: Optional[str] = None
    pages: list[str] = field(default_factory=list)  # per-page text if needed


# ---------------------------------------------------------------------------
# Core extractor  (synchronous — runs in a thread via asyncio.to_thread)
# ---------------------------------------------------------------------------

def _extract_sync(pdf_path: Path) -> ParseResult:
    """
    Open *pdf_path* with PyMuPDF, extract text and metadata, then close.
    Raises FileNotFoundError if the path does not exist.
    Raises fitz.FileDataError if the file is not a valid PDF.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc = fitz.open(str(pdf_path))
    try:
        pages: list[str] = []
        for page in doc:
            pages.append(page.get_text("text"))   # type: ignore[attr-defined]

        full_text = "\n".join(pages)
        meta = doc.metadata or {}

        return ParseResult(
            text=full_text,
            text_length=len(full_text),
            word_count=len(full_text.split()),
            page_count=doc.page_count,
            pages=pages,
            pdf_title=meta.get("title") or None,
            pdf_author=meta.get("author") or None,
            pdf_subject=meta.get("subject") or None,
            pdf_producer=meta.get("producer") or None,
        )
    finally:
        doc.close()


# ---------------------------------------------------------------------------
# Async wrapper
# ---------------------------------------------------------------------------

async def parse_pdf(pdf_path: str | Path) -> ParseResult:
    """
    Asynchronously extract text and metadata from a PDF.

    Offloads the blocking PyMuPDF call to a thread pool so the event
    loop is never stalled.

    Args:
        pdf_path: Absolute or relative path to the PDF file.

    Returns:
        ParseResult with extracted text, counts, and metadata.

    Raises:
        FileNotFoundError: If the file does not exist.
        fitz.FileDataError: If the file is not a valid/readable PDF.
    """
    path = Path(pdf_path)
    logger.debug("Parsing PDF: {}", path)
    result: ParseResult = await asyncio.to_thread(_extract_sync, path)
    logger.info(
        "PDF parsed — pages={} words={} chars={}",
        result.page_count,
        result.word_count,
        result.text_length,
    )
    return result

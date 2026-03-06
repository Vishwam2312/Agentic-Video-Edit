"""
models/document.py
──────────────────
Pydantic schemas for the `documents` MongoDB collection.

A ParsedDocument holds the full extracted text and metadata from a
research-paper PDF.  It is created immediately after upload and linked
to its parent Project via `project_id`.
"""

from __future__ import annotations

from typing import Optional

from pydantic import Field

from backend.models.base import MongoBaseModel, PyObjectId


# ── Stored document ──────────────────────────────────────────────────────────

class ParsedDocumentDocument(MongoBaseModel):
    """Full document as stored in MongoDB."""

    project_id: PyObjectId = Field(..., description="Parent project _id")
    original_filename: str
    upload_path: str

    # ── Extracted content ────────────────────────────────────────────────────
    text: str = Field(default="", description="Full plain-text extracted from the PDF")
    text_length: int = Field(default=0, description="Character count of extracted text")
    page_count: int = Field(default=0)
    word_count: int = Field(default=0)

    # ── PDF metadata (from document info dict) ────────────────────────────────
    pdf_title: Optional[str] = None
    pdf_author: Optional[str] = None
    pdf_subject: Optional[str] = None
    pdf_producer: Optional[str] = None


# ── Request / response schemas ───────────────────────────────────────────────

class ParsedDocumentCreate(MongoBaseModel):
    project_id: PyObjectId
    original_filename: str
    upload_path: str
    text: str = ""
    text_length: int = 0
    page_count: int = 0
    word_count: int = 0
    pdf_title: Optional[str] = None
    pdf_author: Optional[str] = None
    pdf_subject: Optional[str] = None
    pdf_producer: Optional[str] = None


class UploadResponse(MongoBaseModel):
    """Response returned from POST /upload/paper."""

    document_id: str = Field(..., description="MongoDB _id of the ParsedDocument")
    project_id: str = Field(..., description="MongoDB _id of the created Project")
    file_path: str = Field(..., description="Relative storage path of the uploaded PDF")
    original_filename: str
    page_count: int
    text_length: int
    word_count: int
    pdf_title: Optional[str] = None
    pdf_author: Optional[str] = None

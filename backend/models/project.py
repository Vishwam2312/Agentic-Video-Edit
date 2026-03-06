"""
models/project.py
─────────────────
Pydantic schemas for the `projects` MongoDB collection.

A Project is the top-level entity that groups a research-paper upload
with all downstream artefacts (scripts, scenes, videos).
"""

from __future__ import annotations

from enum import StrEnum
from typing import Optional

from pydantic import Field

from backend.models.base import MongoBaseModel


class ProjectStatus(StrEnum):
    PENDING    = "pending"
    PROCESSING = "processing"
    COMPLETED  = "completed"
    FAILED     = "failed"


# ── Stored document ──────────────────────────────────────────────────────────

class ProjectDocument(MongoBaseModel):
    """Full document as stored in MongoDB."""

    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.PENDING
    original_filename: str
    upload_path: str                  # relative path under storage/uploads/
    page_count: Optional[int] = None
    text_length: Optional[int] = None # character count from PDF parser
    error_message: Optional[str] = None


# ── Request / response schemas ───────────────────────────────────────────────

class ProjectCreate(MongoBaseModel):
    """Payload accepted when creating a new project."""

    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    original_filename: str
    upload_path: str


class ProjectUpdate(MongoBaseModel):
    """Partial fields that may be updated."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    page_count: Optional[int] = None
    text_length: Optional[int] = None
    error_message: Optional[str] = None


class ProjectResponse(MongoBaseModel):
    """Outbound API response — excludes internal paths."""

    title: str
    description: Optional[str] = None
    status: ProjectStatus
    original_filename: str
    page_count: Optional[int] = None

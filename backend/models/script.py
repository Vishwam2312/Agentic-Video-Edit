"""
models/script.py
────────────────
Pydantic schemas for the `scripts` MongoDB collection.

A Script is the AI-generated narration text derived from a Project's PDF.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.models.base import MongoBaseModel, PyObjectId


class ScriptStatus(StrEnum):
    PENDING    = "pending"
    GENERATING = "generating"
    READY      = "ready"
    FAILED     = "failed"


# ── Section schema ────────────────────────────────────────────────────────────

class ScriptSection(BaseModel):
    """A single titled section of the generated script."""
    heading: str
    text: str


# ── Stored document ──────────────────────────────────────────────────────────

class ScriptDocument(MongoBaseModel):
    """Full document as stored in MongoDB."""

    project_id: PyObjectId = Field(..., description="Parent project _id")
    status: ScriptStatus = ScriptStatus.PENDING
    title: Optional[str] = None           # AI-generated video title
    sections: Optional[list[ScriptSection]] = None   # structured sections
    content: Optional[str] = None         # flat narration text (full_text)
    word_count: Optional[int] = None
    estimated_duration_s: Optional[float] = None   # approx audio length
    model_used: Optional[str] = None      # e.g. "gpt-4o-mini"
    error_message: Optional[str] = None


# ── Request / response schemas ───────────────────────────────────────────────

class ScriptCreate(MongoBaseModel):
    project_id: PyObjectId
    model_used: Optional[str] = None


class ScriptUpdate(MongoBaseModel):
    status: Optional[ScriptStatus] = None
    title: Optional[str] = None
    sections: Optional[list[ScriptSection]] = None
    content: Optional[str] = None
    word_count: Optional[int] = None
    estimated_duration_s: Optional[float] = None
    model_used: Optional[str] = None
    error_message: Optional[str] = None


class ScriptResponse(MongoBaseModel):
    project_id: PyObjectId
    status: ScriptStatus
    title: Optional[str] = None
    sections: Optional[list[ScriptSection]] = None
    content: Optional[str] = None
    word_count: Optional[int] = None


# ── AI generation request / response ─────────────────────────────────────────

class GenerateScriptRequest(BaseModel):
    """Body for POST /script/generate-script."""
    project_id: str = Field(..., description="Project whose parsed document will be used")
    model: Optional[str] = Field(
        default=None,
        description="Override the default LLM model (e.g. 'gpt-4o', 'llama3')"
    )


class GenerateScriptResponse(BaseModel):
    """Response returned by POST /script/generate-script."""
    model_config = ConfigDict(protected_namespaces=())

    script_id: str
    project_id: str
    status: ScriptStatus
    title: str
    sections: list[ScriptSection]
    word_count: int
    model_used: str
    estimated_duration_s: Optional[float] = None
    model_used: Optional[str] = None

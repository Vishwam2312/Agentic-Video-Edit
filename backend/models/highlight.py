"""
models/highlight.py
────────────────────
Pydantic models for highlight detection.

A `HighlightDocument` stores detected highlights for a project or individual
scene video.  Each detected segment is stored as a nested `HighlightSegmentDoc`.
"""

from __future__ import annotations

from typing import Optional

from pydantic import ConfigDict, Field

from backend.models.base import MongoBaseModel, PyObjectId


# ── Embedded segment ──────────────────────────────────────────────────────────

class HighlightSegmentDoc(MongoBaseModel):
    """One contiguous highlight segment inside a video."""

    model_config = ConfigDict(populate_by_name=True)

    start_s: float = 0.0
    end_s: float = 0.0
    label: str = ""
    score: float = Field(default=0.5, ge=0.0, le=1.0)
    reason: str = ""
    focus_words: list[str] = Field(default_factory=list)

    @property
    def duration_s(self) -> float:
        return max(0.0, self.end_s - self.start_s)


# ── Top-level document ───────────────────────────────────────────────────────

class HighlightDocument(MongoBaseModel):
    """MongoDB document — one per video highlight analysis run."""

    model_config = ConfigDict(
        populate_by_name=True,
        protected_namespaces=(),
    )

    project_id: Optional[PyObjectId] = None
    video_id: Optional[PyObjectId] = None
    scene_id: Optional[PyObjectId] = None

    # Source video that was analysed
    video_path: str = ""
    transcript: str = ""

    # Analysis results
    segments: list[HighlightSegmentDoc] = Field(default_factory=list)
    segment_count: int = 0
    model_used: str = ""
    status: str = "pending"          # pending | ready | error
    error_message: Optional[str] = None


class HighlightCreate(MongoBaseModel):
    project_id: Optional[PyObjectId] = None
    video_id: Optional[PyObjectId] = None
    scene_id: Optional[PyObjectId] = None
    video_path: str
    transcript: str
    segments: list[HighlightSegmentDoc] = Field(default_factory=list)
    segment_count: int = 0
    model_used: str = ""
    status: str = "ready"


# ── API request / response ────────────────────────────────────────────────────

class GenerateHighlightsRequest(MongoBaseModel):
    """
    Request body for ``POST /highlight/generate-highlights``.

    One of ``project_id``, ``video_id``, or ``scene_id`` must be supplied.
    The backend resolves the video file and transcript automatically from those
    references.

    Optional overrides
    ------------------
    transcript_override:
        Provide a custom transcript instead of loading from stored scenes.
    model:
        Override the configured OpenAI model (must support vision / image inputs).
    frame_interval_s:
        Extract one frame every N seconds (default 3).
    """

    model_config = ConfigDict(protected_namespaces=())

    project_id: Optional[PyObjectId] = None
    video_id: Optional[PyObjectId] = None
    scene_id: Optional[PyObjectId] = None

    transcript_override: Optional[str] = None
    model: Optional[str] = None
    frame_interval_s: int = Field(default=3, ge=1, le=30)


class GenerateHighlightsResponse(MongoBaseModel):
    """Response body returned after highlight detection completes."""

    highlight_id: str
    project_id: Optional[str] = None
    video_id: Optional[str] = None
    scene_id: Optional[str] = None
    video_path: str
    segment_count: int
    segments: list[dict]
    model_used: str
    status: str

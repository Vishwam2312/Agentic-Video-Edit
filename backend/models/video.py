"""
models/video.py
───────────────
Pydantic schemas for the `videos` MongoDB collection.

A Video is the final assembled output file for a Project.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, Field

from backend.models.base import MongoBaseModel, PyObjectId


class VideoStatus(StrEnum):
    PENDING    = "pending"
    ASSEMBLING = "assembling"
    READY      = "ready"
    FAILED     = "failed"


# ── Stored document ──────────────────────────────────────────────────────────

class VideoDocument(MongoBaseModel):
    """Full document as stored in MongoDB."""

    project_id: PyObjectId = Field(..., description="Parent project _id")
    status: VideoStatus = VideoStatus.PENDING
    scene_count: Optional[int] = None
    total_duration_s: Optional[float] = None
    output_path: Optional[str] = None          # storage/final/<file>
    file_size_bytes: Optional[int] = None
    resolution: Optional[str] = None           # e.g. "1920x1080"
    fps: Optional[int] = None
    error_message: Optional[str] = None


# ── Request / response schemas ───────────────────────────────────────────────

class VideoCreate(MongoBaseModel):
    project_id: PyObjectId
    scene_count: Optional[int] = None


class VideoUpdate(MongoBaseModel):
    status: Optional[VideoStatus] = None
    total_duration_s: Optional[float] = None
    output_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    resolution: Optional[str] = None
    fps: Optional[int] = None
    error_message: Optional[str] = None


class VideoResponse(MongoBaseModel):
    project_id: PyObjectId
    status: VideoStatus
    scene_count: Optional[int] = None
    total_duration_s: Optional[float] = None
    resolution: Optional[str] = None
    fps: Optional[int] = None


# ── Export request / response ───────────────────────────────────────────────────

class ExportVideoRequest(BaseModel):
    """Body for POST /export/export-video."""
    project_id: str = Field(..., description="Project whose synced scenes will be concatenated")
    output_stem: Optional[str] = Field(
        default=None,
        description="Optional base filename (no extension) for the output MP4",
    )


class ExportVideoResponse(BaseModel):
    """Response returned by POST /export/export-video."""
    video_id: str
    project_id: str
    output_path: str    # relative path inside storage/final/
    file_size_bytes: int
    scene_count: int
    status: VideoStatus
    file_size_bytes: Optional[int] = None

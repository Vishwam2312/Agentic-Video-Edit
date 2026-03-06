"""
models/scene.py
───────────────
Pydantic schemas for the `scenes` MongoDB collection.

A Scene is one visual segment of the final video, derived from a Script.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.models.base import MongoBaseModel, PyObjectId


class SceneStatus(StrEnum):
    PENDING   = "pending"
    RENDERING = "rendering"
    READY     = "ready"
    FAILED    = "failed"


# ── Stored document ──────────────────────────────────────────────────────────

class SceneDocument(MongoBaseModel):
    """Full document as stored in MongoDB."""

    project_id: PyObjectId = Field(..., description="Parent project _id")
    script_id: PyObjectId = Field(..., description="Parent script _id")
    index: int = Field(..., ge=0, description="0-based scene order")
    status: SceneStatus = SceneStatus.PENDING
    narration_text: str = Field(..., min_length=1)
    visual_description: Optional[str] = None   # prompt for animation agent
    focus_words: list[str] = Field(default_factory=list)  # key terms to highlight
    animation_path: Optional[str] = None       # storage/animations/<file>.py
    animation_code: Optional[str] = None       # raw Manim Python source
    rendered_video_path: Optional[str] = None  # storage/videos/<file>.mp4
    synced_video_path: Optional[str] = None    # storage/videos/<stem>_synced.mp4
    audio_path: Optional[str] = None           # storage/audio/<file>
    duration_s: Optional[float] = None
    error_message: Optional[str] = None


# ── Request / response schemas ───────────────────────────────────────────────

class SceneCreate(MongoBaseModel):
    project_id: PyObjectId
    script_id: PyObjectId
    index: int = Field(..., ge=0)
    narration_text: str = Field(..., min_length=1)
    visual_description: Optional[str] = None
    focus_words: list[str] = Field(default_factory=list)


class SceneUpdate(MongoBaseModel):
    status: Optional[SceneStatus] = None
    visual_description: Optional[str] = None
    focus_words: Optional[list[str]] = None
    animation_path: Optional[str] = None
    animation_code: Optional[str] = None
    rendered_video_path: Optional[str] = None
    synced_video_path: Optional[str] = None
    audio_path: Optional[str] = None
    duration_s: Optional[float] = None
    error_message: Optional[str] = None


class SceneResponse(MongoBaseModel):
    project_id: PyObjectId
    script_id: PyObjectId
    index: int
    status: SceneStatus
    narration_text: str
    visual_description: Optional[str] = None
    focus_words: list[str] = Field(default_factory=list)
    duration_s: Optional[float] = None


# ── AI generation request / response ─────────────────────────────────────────────────

class GenerateScenesRequest(BaseModel):
    """Body for POST /scene/generate-scenes."""
    project_id: str = Field(..., description="Parent project _id")
    script_id: str = Field(..., description="Script to break into scenes")
    model: Optional[str] = Field(
        default=None,
        description="Override the default LLM model",
    )


class SceneOut(BaseModel):
    """Single scene entry in GenerateScenesResponse."""
    scene_id: str          # MongoDB ObjectId string
    index: int             # 0-based position
    narration_text: str
    visual_description: str
    focus_words: list[str]


class GenerateScenesResponse(BaseModel):
    """Response returned by POST /scene/generate-scenes."""
    model_config = ConfigDict(protected_namespaces=())

    project_id: str
    script_id: str
    scene_count: int
    model_used: str
    scenes: list[SceneOut]


# ── Animation generation request / response ───────────────────────────────────

class GenerateAnimationRequest(BaseModel):
    """Body for POST /animation/generate-animation."""
    scene_id: str = Field(..., description="Scene to generate Manim code for")
    model: Optional[str] = Field(
        default=None,
        description="Override the default LLM model",
    )


class GenerateAnimationResponse(BaseModel):
    """Response returned by POST /animation/generate-animation."""
    model_config = ConfigDict(protected_namespaces=())

    scene_id: str
    animation_path: str    # relative path to the saved .py file
    model_used: str
    manim_code: str        # full Manim Python source


# ── Render request / response ──────────────────────────────────────────────────────

class RenderSceneRequest(BaseModel):
    """Body for POST /animation/render-scene."""
    scene_id: str = Field(..., description="Scene whose animation_code will be rendered")
    quality: str = Field(
        default="l",
        description="Manim quality flag: 'l' (480p), 'm' (720p), 'h' (1080p)",
        pattern="^[lmhk]$",
    )


class RenderSceneResponse(BaseModel):
    """Response returned by POST /animation/render-scene."""
    scene_id: str
    video_path: str        # relative path to the MP4 in storage/videos/
    status: SceneStatus


# ── TTS request / response ───────────────────────────────────────────────────────

class GenerateTTSRequest(BaseModel):
    """Body for POST /tts/generate-tts."""
    scene_id: str = Field(..., description="Scene whose narration_text will be synthesized")
    tts_model: Optional[str] = Field(
        default=None,
        description="Override the Coqui TTS model (e.g. tts_models/en/vctk/vits)",
    )


class GenerateTTSResponse(BaseModel):
    """Response returned by POST /tts/generate-tts."""
    scene_id: str
    audio_path: str   # relative path to the WAV in storage/audio/
    status: SceneStatus


# ── Sync request / response ────────────────────────────────────────────────────────

class SyncSceneRequest(BaseModel):
    """Body for POST /sync/sync-scene."""
    scene_id: str = Field(..., description="Scene with both rendered_video_path and audio_path set")


class SyncSceneResponse(BaseModel):
    """Response returned by POST /sync/sync-scene."""
    scene_id: str
    synced_video_path: str   # storage/videos/<stem>_synced.mp4
    status: SceneStatus

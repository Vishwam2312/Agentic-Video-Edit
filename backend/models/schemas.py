"""
models/schemas.py
──────────────────
Pydantic schemas for the hierarchical Scene → SubScene structure.

Hierarchy
---------
Scene
├── scene_id        (str, UUID-style or MongoDB ObjectId hex)
├── scene_title     (str)
├── project_id      (str)
└── subscenes       (list[SubScene])
        ├── subscene_id         (str)
        ├── text                (str)
        ├── visual_description  (str)
        ├── video_ids           (list[str])
        └── created_at          (datetime, UTC)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# SubScene schemas
# ─────────────────────────────────────────────────────────────────────────────

class SubSceneCreate(BaseModel):
    """
    Payload for creating a new subscene.

    ``subscene_id`` is generated automatically if not supplied.
    ``video_ids`` starts as an empty list and is populated as video
    chunks are rendered and attached.
    """

    subscene_id: str = Field(
        default_factory=lambda: uuid4().hex,
        description="Unique identifier for this subscene. Auto-generated if omitted.",
    )
    text: str = Field(
        ...,
        description="Narration / spoken text for this subscene.",
    )
    visual_description: str = Field(
        default="",
        description="Description of what should be shown visually.",
    )
    video_ids: list[str] = Field(
        default_factory=list,
        description="Ordered list of video chunk IDs that compose this subscene.",
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Arbitrary key-value pairs for tool-specific data (e.g. duration, style).",
    )


class SubSceneUpdate(BaseModel):
    """
    Payload for partially updating an existing subscene.

    All fields are optional; only supplied fields are applied.
    """

    text: Optional[str] = None
    visual_description: Optional[str] = None
    video_ids: Optional[list[str]] = None
    metadata: Optional[dict] = None


class SubSceneResponse(BaseModel):
    """
    Full subscene representation returned from the API.

    ``created_at`` is always present in responses (set at insertion time).
    """

    subscene_id: str
    text: str
    visual_description: str
    video_ids: list[str]
    metadata: dict
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
    )

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Scene schemas
# ─────────────────────────────────────────────────────────────────────────────

class SceneCreate(BaseModel):
    """
    Payload for creating a new scene.

    ``scene_id`` is generated automatically if not supplied.
    ``subscenes`` may be provided inline at creation time or added later
    via dedicated subscene endpoints.
    """

    scene_id: str = Field(
        default_factory=lambda: uuid4().hex,
        description="Unique identifier for this scene. Auto-generated if omitted.",
    )
    scene_title: str = Field(
        ...,
        description="Human-readable title for this scene.",
    )
    project_id: str = Field(
        ...,
        description="ID of the parent project this scene belongs to.",
    )
    subscenes: list[SubSceneCreate] = Field(
        default_factory=list,
        description="Ordered list of subscenes that make up this scene.",
    )


class SceneResponse(BaseModel):
    """
    Full scene representation returned from the API.

    ``subscenes`` is always a list of :class:`SubSceneResponse` objects,
    so every subscene includes its ``created_at`` timestamp.
    """

    scene_id: str
    scene_title: str
    project_id: str
    subscenes: list[SubSceneResponse]

    model_config = {"from_attributes": True}

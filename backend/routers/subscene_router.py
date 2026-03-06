"""
routers/subscene_router.py
───────────────────────────
Subscene creation, update, and video-attachment endpoints.

Routes
------
POST /subscene/create     — append a new subscene to an existing scene document
PUT  /subscene/update     — update fields on an existing subscene
POST /subscene/add-video  — attach a rendered video chunk ID to a subscene
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from backend.services.database import (
    add_video_to_subscene,
    append_subscene,
    db_dependency,
    update_subscene,
)

router = APIRouter(tags=["subscenes"])


# ── Request / Response ────────────────────────────────────────────────────────

class CreateSubsceneRequest(BaseModel):
    scene_id: str
    text: str
    visual_description: str = ""


class SubsceneResponse(BaseModel):
    subscene_id: str
    text: str
    visual_description: str
    video_ids: list[str]
    created_at: datetime


class AddVideoRequest(BaseModel):
    scene_id: str
    subscene_id: str
    video_id: str


class AddVideoResponse(BaseModel):
    scene_id: str
    subscene_id: str
    video_id: str


class UpdateSubsceneRequest(BaseModel):
    scene_id: str
    subscene_id: str
    text: str | None = None
    visual_description: str | None = None


class UpdateSubsceneResponse(BaseModel):
    scene_id: str
    subscene_id: str
    updated_fields: list[str]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/create",
    response_model=SubsceneResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Append a new subscene to an existing scene",
)
async def create_subscene(
    body: CreateSubsceneRequest,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> SubsceneResponse:
    """
    Generates a ``subscene_id``, builds the subscene object, and atomically
    appends it to the parent scene's ``subscenes`` array via MongoDB ``$push``.

    Returns HTTP 404 if the ``scene_id`` does not match any scene document.
    """
    now = datetime.now(tz=timezone.utc)
    subscene = {
        "subscene_id": uuid4().hex,
        "text": body.text,
        "visual_description": body.visual_description,
        "video_ids": [],
        "created_at": now,
    }

    updated = await append_subscene(body.scene_id, subscene, db=db)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scene '{body.scene_id}' not found.",
        )

    return SubsceneResponse(**subscene)


@router.put(
    "/update",
    response_model=UpdateSubsceneResponse,
    summary="Update fields on an existing subscene",
)
async def update_subscene_endpoint(
    body: UpdateSubsceneRequest,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> UpdateSubsceneResponse:
    """
    Partially updates a subscene using the MongoDB positional operator
    (``subscenes.$``), so only the supplied fields are changed.

    Example MongoDB operation when both fields are provided::

        { "$set": { "subscenes.$.text": "...", "subscenes.$.visual_description": "..." } }

    Returns HTTP 404 if the ``scene_id`` or ``subscene_id`` is not found.
    Returns HTTP 400 if no updatable fields are supplied.
    """
    updates = {
        key: value
        for key, value in {
            "text": body.text,
            "visual_description": body.visual_description,
        }.items()
        if value is not None
    }

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Supply at least one field to update: 'text' or 'visual_description'.",
        )

    result = await update_subscene(body.scene_id, body.subscene_id, updates, db=db)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No match for scene_id='{body.scene_id}' "
                f"and subscene_id='{body.subscene_id}'."
            ),
        )

    return UpdateSubsceneResponse(
        scene_id=body.scene_id,
        subscene_id=body.subscene_id,
        updated_fields=list(updates.keys()),
    )


@router.post(
    "/add-video",
    response_model=AddVideoResponse,
    status_code=status.HTTP_200_OK,
    summary="Attach a rendered video chunk ID to a subscene",
)
async def add_video_endpoint(
    body: AddVideoRequest,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> AddVideoResponse:
    """
    Appends ``video_id`` to the target subscene's ``video_ids`` array using
    ``$addToSet``, which prevents duplicate entries.

    Equivalent MongoDB operation::

        { "$addToSet": { "subscenes.$.video_ids": "<video_id>" } }

    Returns HTTP 404 if the ``scene_id`` or ``subscene_id`` is not found.
    """
    result = await add_video_to_subscene(
        body.scene_id, body.subscene_id, body.video_id, db=db
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No match for scene_id='{body.scene_id}' "
                f"and subscene_id='{body.subscene_id}'."
            ),
        )

    return AddVideoResponse(
        scene_id=body.scene_id,
        subscene_id=body.subscene_id,
        video_id=body.video_id,
    )

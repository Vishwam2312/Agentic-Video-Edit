"""
routers/scene_router.py
────────────────────────
Scene creation endpoints using the hierarchical Scene → SubScene model.

Routes
------
POST /scenes/create   — create a new scene with an empty subscenes array
"""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from backend.services.database import create_scene, db_dependency

router = APIRouter(tags=["scenes"])


# ── Request / Response ────────────────────────────────────────────────────────

class CreateSceneRequest(BaseModel):
    project_id: str
    scene_title: str


class CreateSceneResponse(BaseModel):
    scene_id: str
    scene_title: str
    project_id: str
    subscenes: list


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post(
    "/create",
    response_model=CreateSceneResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new scene with an empty subscenes array",
)
async def create_scene_endpoint(
    body: CreateSceneRequest,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> CreateSceneResponse:
    """
    Creates a scene document in MongoDB.

    The ``scene_id`` is generated automatically (UUID hex).
    ``subscenes`` starts as an empty list and can be populated later via
    the subscene append endpoint.
    """
    scene_id = uuid4().hex

    try:
        doc = await create_scene(
            scene_id=scene_id,
            scene_title=body.scene_title,
            project_id=body.project_id,
            subscenes=[],
            db=db,
        )
    except ValueError as exc:
        # Duplicate scene_id — practically impossible with UUID but handled
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return CreateSceneResponse(
        scene_id=doc["_id"],
        scene_title=doc["scene_title"],
        project_id=doc["project_id"],
        subscenes=doc["subscenes"],
    )

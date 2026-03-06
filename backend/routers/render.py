"""
routers/render.py
──────────────────
Initiates per-scene video rendering and tracks the Video document.
Rendered videos are stored in storage/videos/.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.models.video import VideoCreate, VideoDocument, VideoUpdate
from backend.services.database import db_dependency
from backend.services.scene_service import list_scenes_for_project
from backend.services.video_service import (
    create_video,
    get_video_by_id,
    get_video_by_project,
    update_video,
)
from backend.utils.errors import raise_not_found, validate_object_id

router = APIRouter(tags=["Render"])


@router.post(
    "/video/{project_id}",
    response_model=VideoDocument,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate video render for a project",
)
async def initiate_render(
    project_id: str,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> VideoDocument:
    """
    Creates a Video document for the project and counts its ready scenes.
    The render agent picks this up and sets `output_path` when done.
    """
    validate_object_id(project_id, "project_id")
    scenes = await list_scenes_for_project(db, project_id)
    payload = VideoCreate(project_id=project_id, scene_count=len(scenes))
    return await create_video(db, payload)


@router.get(
    "/project/{project_id}",
    response_model=VideoDocument,
    summary="Get the video record for a project",
)
async def get_video_for_project(
    project_id: str,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> VideoDocument:
    validate_object_id(project_id, "project_id")
    doc = await get_video_by_project(db, project_id)
    if not doc:
        raise_not_found("Video", f"project:{project_id}")
    return doc


@router.get(
    "/{video_id}",
    response_model=VideoDocument,
    summary="Get a video record by ID",
)
async def get_video(
    video_id: str,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> VideoDocument:
    validate_object_id(video_id, "video_id")
    doc = await get_video_by_id(db, video_id)
    if not doc:
        raise_not_found("Video", video_id)
    return doc


@router.patch(
    "/{video_id}",
    response_model=VideoDocument,
    summary="Update video status or metadata",
)
async def patch_video(
    video_id: str,
    payload: VideoUpdate,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> VideoDocument:
    """Called by the render agent to set output_path, resolution, fps, etc."""
    validate_object_id(video_id, "video_id")
    doc = await update_video(db, video_id, payload)
    if not doc:
        raise_not_found("Video", video_id)
    return doc


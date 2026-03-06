"""
routers/sync.py
────────────────
Audio-video sync for individual scenes using FFmpeg.
Merges rendered_video_path + audio_path → synced_video_path on the Scene.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.agents.sync_agent import sync_audio_video
from backend.models.scene import (
    SceneDocument,
    SceneStatus,
    SceneUpdate,
    SyncSceneRequest,
    SyncSceneResponse,
)
from backend.services.database import db_dependency
from backend.services.scene_service import (
    get_scene_by_id,
    list_scenes_for_project,
    update_scene,
)
from backend.utils.errors import raise_not_found, validate_object_id

router = APIRouter(tags=["Audio-Video Sync"])


# ---------------------------------------------------------------------------
# FFmpeg sync
# ---------------------------------------------------------------------------

@router.post(
    "/sync-scene",
    response_model=SyncSceneResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Merge rendered video and audio into a single MP4 using FFmpeg",
    description=(
        "Requires the scene to have both rendered_video_path (from /render-scene) "
        "and audio_path (from /generate-tts). Runs FFmpeg to mux them together, "
        "saves the result to storage/videos/<stem>_synced.mp4, and updates the "
        "scene document. Requires FFmpeg on PATH."
    ),
)
async def sync_scene_endpoint(
    payload: SyncSceneRequest,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> SyncSceneResponse:
    validate_object_id(payload.scene_id, "scene_id")

    scene_doc = await get_scene_by_id(db, payload.scene_id)
    if not scene_doc:
        raise_not_found("Scene", payload.scene_id)

    if not scene_doc.rendered_video_path:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Scene has no rendered_video_path. Run POST /api/v1/animation/render-scene first.",
        )
    if not scene_doc.audio_path:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Scene has no audio_path. Run POST /api/v1/tts/generate-tts first.",
        )

    await update_scene(db, payload.scene_id, SceneUpdate(status=SceneStatus.RENDERING))

    stem = f"scene_{scene_doc.index:03d}_synced"
    try:
        synced_path = await sync_audio_video(
            scene_doc.rendered_video_path,
            scene_doc.audio_path,
            output_stem=stem,
        )
    except FileNotFoundError as exc:
        await update_scene(
            db, payload.scene_id,
            SceneUpdate(status=SceneStatus.FAILED, error_message=str(exc)),
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        await update_scene(
            db, payload.scene_id,
            SceneUpdate(status=SceneStatus.FAILED, error_message=str(exc)),
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"FFmpeg sync failed: {exc}",
        ) from exc

    relative = str(synced_path.relative_to(Path(".").resolve()))
    await update_scene(
        db, payload.scene_id,
        SceneUpdate(status=SceneStatus.READY, synced_video_path=relative),
    )

    return SyncSceneResponse(
        scene_id=payload.scene_id,
        synced_video_path=relative,
        status=SceneStatus.READY,
    )


# ---------------------------------------------------------------------------
# Status endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/align/{scene_id}",
    response_model=SceneDocument,
    summary="Mark a scene as rendering (manual trigger)",
)
async def trigger_alignment(
    scene_id: str,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> SceneDocument:
    """
    Validates that both `rendered_video_path` and `audio_path` are present,
    then marks the scene as `rendering`. Use POST /sync-scene for the full pipeline.
    """
    validate_object_id(scene_id, "scene_id")
    doc = await get_scene_by_id(db, scene_id)
    if not doc:
        raise_not_found("Scene", scene_id)
    if not doc.rendered_video_path or not doc.audio_path:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Scene must have both rendered_video_path and audio_path before sync.",
        )
    return await update_scene(db, scene_id, SceneUpdate(status=SceneStatus.RENDERING))


@router.get(
    "/project/{project_id}",
    summary="Get sync status for all scenes in a project",
)
async def project_sync_status(
    project_id: str,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> dict:
    validate_object_id(project_id, "project_id")
    scenes = await list_scenes_for_project(db, project_id)
    summary: dict[str, list[str]] = {s.value: [] for s in SceneStatus}
    for scene in scenes:
        summary[scene.status].append(str(scene.id))
    return {
        "project_id": project_id,
        "total_scenes": len(scenes),
        "by_status": summary,
        "all_ready": all(s.status == SceneStatus.READY for s in scenes),
    }


@router.get(
    "/{scene_id}",
    response_model=SceneDocument,
    summary="Get sync status for a single scene",
)
async def get_sync_status(
    scene_id: str,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> SceneDocument:
    validate_object_id(scene_id, "scene_id")
    doc = await get_scene_by_id(db, scene_id)
    if not doc:
        raise_not_found("Scene", scene_id)
    return doc


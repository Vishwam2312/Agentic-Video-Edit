"""
routers/export.py
──────────────────
Assembles all rendered + synced scene clips into a single final MP4 using
FFmpeg, persists the Video document, and serves the file for download.
Final videos are stored in storage/final/.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.models.video import (
    ExportVideoRequest,
    ExportVideoResponse,
    VideoCreate,
    VideoDocument,
    VideoStatus,
    VideoUpdate,
)
from backend.services.database import db_dependency
from backend.services.video_exporter import assemble_scene, export_final_video
from backend.services.video_service import (
    create_video,
    get_video_by_id,
    get_video_by_project,
    update_video,
)
from backend.utils.errors import raise_not_found, validate_object_id

router = APIRouter(tags=["Export"])


# ---------------------------------------------------------------------------
# FFmpeg export
# ---------------------------------------------------------------------------

@router.post(
    "/export-video",
    response_model=ExportVideoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Concatenate all scene clips into a final MP4 video",
    description=(
        "Fetches all scenes for the project (ordered by index), uses each "
        "scene's synced_video_path (falling back to rendered_video_path), "
        "concatenates them with FFmpeg stream-copy, saves to storage/final/, "
        "and persists a Video document. Requires FFmpeg on PATH."
    ),
)
async def export_video_endpoint(
    payload: ExportVideoRequest,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> ExportVideoResponse:
    validate_object_id(payload.project_id, "project_id")

    # 1. Create (or reuse) a Video document, mark as ASSEMBLING
    video_doc = await get_video_by_project(db, payload.project_id)
    if video_doc:
        video_id = str(video_doc.id)
        await update_video(db, video_id, VideoUpdate(status=VideoStatus.ASSEMBLING))
    else:
        video_doc = await create_video(
            db,
            VideoCreate(project_id=payload.project_id),
        )
        video_id = str(video_doc.id)
        await update_video(db, video_id, VideoUpdate(status=VideoStatus.ASSEMBLING))

    # 2. Assemble scenes from subscene video chunks then concat into final MP4
    stem = payload.output_stem or f"project_{payload.project_id[:8]}_final"
    try:
        output_path = await export_final_video(
            payload.project_id,
            db=db,
            output_stem=stem,
        )
    except (ValueError, FileNotFoundError) as exc:
        await update_video(
            db, video_id,
            VideoUpdate(status=VideoStatus.FAILED, error_message=str(exc)),
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        await update_video(
            db, video_id,
            VideoUpdate(status=VideoStatus.FAILED, error_message=str(exc)),
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"FFmpeg export failed: {exc}",
        ) from exc

    # 3. Persist the result
    relative = str(output_path.relative_to(Path(".").resolve()))
    file_size = output_path.stat().st_size
    await update_video(
        db, video_id,
        VideoUpdate(
            status=VideoStatus.READY,
            output_path=relative,
            file_size_bytes=file_size,
        ),
    )

    return ExportVideoResponse(
        video_id=video_id,
        project_id=payload.project_id,
        output_path=relative,
        file_size_bytes=file_size,
        scene_count=0,
        status=VideoStatus.READY,
    )


# ---------------------------------------------------------------------------
# Legacy / status / download endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/assemble/{project_id}",
    response_model=VideoDocument,
    summary="Mark a project video as assembling (manual trigger)",
)
async def assemble_video(
    project_id: str,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> VideoDocument:
    """
    Marks the project's Video document as `assembling`.
    Use POST /export-video for the full automated pipeline.
    """
    validate_object_id(project_id, "project_id")
    doc = await get_video_by_project(db, project_id)
    if not doc:
        raise_not_found("Video", f"project:{project_id}")
    return await update_video(db, str(doc.id), VideoUpdate(status=VideoStatus.ASSEMBLING))


@router.get(
    "/project/{project_id}",
    response_model=VideoDocument,
    summary="Get export status for a project",
)
async def export_status_for_project(
    project_id: str,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> VideoDocument:
    validate_object_id(project_id, "project_id")
    doc = await get_video_by_project(db, project_id)
    if not doc:
        raise_not_found("Video", f"project:{project_id}")
    return doc


@router.get(
    "/download/{video_id}",
    summary="Download the final assembled video",
    response_class=FileResponse,
)
async def download_video(
    video_id: str,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
):
    """Streams the final video file to the client."""
    validate_object_id(video_id, "video_id")
    doc = await get_video_by_id(db, video_id)
    if not doc:
        raise_not_found("Video", video_id)
    if doc.status != VideoStatus.READY or not doc.output_path:
        raise HTTPException(
            status_code=status.HTTP_425_TOO_EARLY,
            detail=f"Video is not ready for download. Current status: '{doc.status}'.",
        )
    file_path = Path(doc.output_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video file not found on disk. It may have been moved or deleted.",
        )
    return FileResponse(
        path=str(file_path),
        media_type="video/mp4",
        filename=file_path.name,
    )


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


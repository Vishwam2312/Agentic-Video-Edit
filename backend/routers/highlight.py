"""
routers/highlight.py
─────────────────────
Highlight detection endpoints.

POST /highlight/generate-highlights
    Accepts a project_id, video_id, or scene_id.
    Resolves the relevant video file and transcript from stored documents,
    runs the highlight detection agent, saves results to MongoDB, and
    returns the structured highlight segments.

GET  /highlight/{highlight_id}
    Retrieve a previously generated highlight analysis by its Mongo ID.

GET  /highlight/project/{project_id}
    List all highlight analyses for a project, newest first.
"""

from __future__ import annotations

from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.agents.highlight_agent import generate_highlights
from backend.models.highlight import (
    GenerateHighlightsRequest,
    GenerateHighlightsResponse,
    HighlightCreate,
    HighlightSegmentDoc,
)
from backend.services.database import Collections, db_dependency
from fastapi import HTTPException, status as http_status


def _bad_request(detail: str) -> HTTPException:
    return HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=detail)


def _not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=detail)

router = APIRouter(tags=["highlights"])


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _to_oid(value: str | None) -> ObjectId | None:
    if not value:
        return None
    try:
        return ObjectId(str(value))
    except Exception:
        return None


async def _resolve_source(
    req: GenerateHighlightsRequest,
    db: AsyncIOMotorDatabase,
) -> tuple[str, str, str | None, str | None, str | None]:
    """
    Return (video_path, transcript, project_id_str, video_id_str, scene_id_str).

    Resolution priority: scene_id → video_id → project_id
    """
    project_id_str: str | None = str(req.project_id) if req.project_id else None
    video_id_str: str | None = str(req.video_id) if req.video_id else None
    scene_id_str: str | None = str(req.scene_id) if req.scene_id else None

    # ── By scene ──────────────────────────────────────────────────────────────
    if scene_id_str:
        oid = _to_oid(scene_id_str)
        scene_doc = await db[Collections.SCENES].find_one({"_id": oid})
        if not scene_doc:
            raise _not_found(f"Scene {scene_id_str} not found")

        video_path: str = (
            scene_doc.get("synced_video_path")
            or scene_doc.get("rendered_video_path")
            or ""
        )
        if not video_path:
            raise _bad_request(
                f"Scene {scene_id_str} has no rendered or synced video. "
                "Run /render-scene and /sync-scene first."
            )

        transcript: str = req.transcript_override or scene_doc.get("narration_text", "")
        return (
            video_path,
            transcript,
            str(scene_doc.get("project_id", "")),
            video_id_str,
            scene_id_str,
        )

    # ── By video_id ───────────────────────────────────────────────────────────
    if video_id_str:
        oid = _to_oid(video_id_str)
        video_doc = await db[Collections.VIDEOS].find_one({"_id": oid})
        if not video_doc:
            raise _not_found(f"Video {video_id_str} not found")

        video_path = video_doc.get("output_path", "")
        if not video_path:
            raise _bad_request(f"Video {video_id_str} has no output_path yet.")

        # Build transcript from associated scenes
        proj_oid = video_doc.get("project_id")
        transcript = req.transcript_override or await _scenes_transcript(db, proj_oid)
        return (
            video_path,
            transcript,
            str(proj_oid) if proj_oid else project_id_str,
            video_id_str,
            scene_id_str,
        )

    # ── By project_id (default) ───────────────────────────────────────────────
    if project_id_str:
        proj_oid = _to_oid(project_id_str)

        # Find the most recent "ready" video export for this project
        video_doc = await db[Collections.VIDEOS].find_one(
            {"project_id": proj_oid, "status": "ready"},
            sort=[("created_at", -1)],
        )
        if not video_doc:
            raise _bad_request(
                f"No exported video found for project {project_id_str}. "
                "Run /export/export-video first."
            )

        video_path = video_doc.get("output_path", "")
        if not video_path:
            raise _bad_request(
                f"Exported video for project {project_id_str} has no output_path."
            )

        transcript = req.transcript_override or await _scenes_transcript(db, proj_oid)
        return (
            video_path,
            transcript,
            project_id_str,
            str(video_doc["_id"]),
            scene_id_str,
        )

    raise _bad_request("Supply at least one of: project_id, video_id, scene_id.")


async def _scenes_transcript(db: AsyncIOMotorDatabase, project_oid) -> str:
    """
    Build a transcript string by joining narration_text of all scenes for
    a project, sorted by scene index.
    """
    cursor = db[Collections.SCENES].find(
        {"project_id": project_oid},
        sort=[("index", 1)],
    )
    scenes = await cursor.to_list(length=None)
    parts: list[str] = []
    for s in scenes:
        text = (s.get("narration_text") or "").strip()
        if text:
            idx = s.get("index", len(parts))
            parts.append(f"[Scene {idx}] {text}")
    return "\n\n".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/generate-highlights",
    response_model=GenerateHighlightsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Detect highlight segments in a video using vision + transcript",
)
async def generate_highlights_endpoint(
    req: GenerateHighlightsRequest,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> GenerateHighlightsResponse:
    """
    Run highlight detection on a stored video.

    **Resolution order** for locating the video and transcript:
    1. ``scene_id`` — uses that scene's synced/rendered video + narration
    2. ``video_id`` — uses the exported video file + project transcript
    3. ``project_id`` — uses the most recent exported video + project transcript

    Returns a structured list of highlight segments with start/end timestamps,
    a label, confidence score, and reason.
    """
    video_path, transcript, project_id_str, video_id_str, scene_id_str = (
        await _resolve_source(req, db)
    )

    resolved_model = req.model or None  # agent uses settings.openai_model if None

    logger.info(
        "Starting highlight detection — video={} model={}",
        video_path,
        resolved_model,
    )

    # ── Run agent ─────────────────────────────────────────────────────────────
    try:
        segments = await generate_highlights(
            video_path=video_path,
            transcript=transcript,
            model=resolved_model,
            frame_interval_s=req.frame_interval_s,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Highlight agent error: {exc}",
        ) from exc

    logger.info("Highlight detection complete — {} segments found", len(segments))

    # ── Persist to MongoDB ────────────────────────────────────────────────────
    segment_docs = [
        HighlightSegmentDoc(
            start_s=s.start_s,
            end_s=s.end_s,
            label=s.label,
            score=s.score,
            reason=s.reason,
            focus_words=s.focus_words,
        )
        for s in segments
    ]

    doc = HighlightCreate(
        project_id=project_id_str,    # type: ignore[arg-type]
        video_id=video_id_str,         # type: ignore[arg-type]
        scene_id=scene_id_str,         # type: ignore[arg-type]
        video_path=video_path,
        transcript=transcript[:2000],  # store summary, not full text
        segments=segment_docs,
        segment_count=len(segment_docs),
        model_used=resolved_model or "default",
        status="ready",
    )

    payload = doc.model_dump(by_alias=True, exclude_none=True)
    payload["created_at"] = datetime.now(tz=timezone.utc)

    result = await db[Collections.HIGHLIGHTS].insert_one(payload)
    highlight_id = str(result.inserted_id)

    return GenerateHighlightsResponse(
        highlight_id=highlight_id,
        project_id=project_id_str,
        video_id=video_id_str,
        scene_id=scene_id_str,
        video_path=video_path,
        segment_count=len(segments),
        segments=[s.to_dict() for s in segments],
        model_used=resolved_model or "default",
        status="ready",
    )


@router.get(
    "/{highlight_id}",
    summary="Retrieve a highlight analysis by ID",
)
async def get_highlight(
    highlight_id: str,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
):
    oid = _to_oid(highlight_id)
    if not oid:
        raise _bad_request(f"Invalid highlight_id: {highlight_id!r}")

    doc = await db[Collections.HIGHLIGHTS].find_one({"_id": oid})
    if not doc:
        raise _not_found(f"Highlight analysis {highlight_id} not found")

    doc["id"] = str(doc.pop("_id"))
    if "project_id" in doc and doc["project_id"]:
        doc["project_id"] = str(doc["project_id"])
    if "video_id" in doc and doc["video_id"]:
        doc["video_id"] = str(doc["video_id"])
    if "scene_id" in doc and doc["scene_id"]:
        doc["scene_id"] = str(doc["scene_id"])
    return doc


@router.get(
    "/project/{project_id}",
    summary="List all highlight analyses for a project",
)
async def list_highlights_for_project(
    project_id: str,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
):
    proj_oid = _to_oid(project_id)
    if not proj_oid:
        raise _bad_request(f"Invalid project_id: {project_id!r}")

    cursor = db[Collections.HIGHLIGHTS].find(
        {"project_id": proj_oid},
        sort=[("created_at", -1)],
    )
    docs = await cursor.to_list(length=50)
    for doc in docs:
        doc["id"] = str(doc.pop("_id"))
        for field_name in ("project_id", "video_id", "scene_id"):
            if doc.get(field_name):
                doc[field_name] = str(doc[field_name])
    return docs

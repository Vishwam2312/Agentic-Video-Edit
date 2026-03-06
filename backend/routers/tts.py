"""
routers/tts.py
───────────────
Coqui TTS synthesis for a scene and tracks audio path/status.
Audio files are stored in storage/audio/ and tracked on the Scene document.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.agents.tts_agent import generate_audio
from backend.config import settings
from backend.models.scene import (
    GenerateTTSRequest,
    GenerateTTSResponse,
    SceneDocument,
    SceneStatus,
    SceneUpdate,
)
from backend.services.database import db_dependency
from backend.services.scene_service import get_scene_by_id, update_scene
from backend.utils.errors import raise_not_found, validate_object_id

router = APIRouter(tags=["Text-to-Speech"])


# ---------------------------------------------------------------------------
# Coqui TTS synthesis
# ---------------------------------------------------------------------------

@router.post(
    "/generate-tts",
    response_model=GenerateTTSResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Synthesize speech for a scene using Coqui TTS",
    description=(
        "Reads the scene's narration_text, runs Coqui TTS locally, saves the "
        "output WAV to storage/audio/, updates the scene document with the "
        "audio path, and returns the result. "
        "Requires Coqui TTS: pip install TTS"
    ),
)
async def generate_tts_endpoint(
    payload: GenerateTTSRequest,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> GenerateTTSResponse:
    validate_object_id(payload.scene_id, "scene_id")

    # 1. Fetch the scene
    scene_doc = await get_scene_by_id(db, payload.scene_id)
    if not scene_doc:
        raise_not_found("Scene", payload.scene_id)

    if not scene_doc.narration_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Scene has no narration_text.",
        )

    # 2. Mark as rendering
    await update_scene(db, payload.scene_id, SceneUpdate(status=SceneStatus.RENDERING))

    # 3. Run TTS
    stem = f"scene_{scene_doc.index:03d}_{uuid.uuid4().hex[:8]}"
    try:
        wav_path = await generate_audio(
            scene_doc.narration_text,
            stem=stem,
            model_name=payload.tts_model,
        )
    except ImportError as exc:
        await update_scene(
            db, payload.scene_id,
            SceneUpdate(status=SceneStatus.FAILED, error_message=str(exc)),
        )
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        await update_scene(
            db, payload.scene_id,
            SceneUpdate(status=SceneStatus.FAILED, error_message=str(exc)),
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"TTS synthesis failed: {exc}",
        ) from exc

    # 4. Persist audio path on scene
    relative = str(wav_path.relative_to(Path(".").resolve()))
    await update_scene(
        db, payload.scene_id,
        SceneUpdate(status=SceneStatus.READY, audio_path=relative),
    )

    return GenerateTTSResponse(
        scene_id=payload.scene_id,
        audio_path=relative,
        status=SceneStatus.READY,
    )


# ---------------------------------------------------------------------------
# Legacy / status endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/synthesize/{scene_id}",
    response_model=SceneDocument,
    summary="Mark a scene as rendering (manual trigger)",
)
async def trigger_synthesis(
    scene_id: str,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> SceneDocument:
    """
    Marks the scene as `rendering`. Use POST /generate-tts for the full pipeline.
    """
    validate_object_id(scene_id, "scene_id")
    doc = await get_scene_by_id(db, scene_id)
    if not doc:
        raise_not_found("Scene", scene_id)
    return await update_scene(db, scene_id, SceneUpdate(status=SceneStatus.RENDERING))


@router.get(
    "/{scene_id}",
    response_model=SceneDocument,
    summary="Get TTS status for a scene",
)
async def get_tts_status(
    scene_id: str,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> SceneDocument:
    """Returns the full scene document including audio_path and status."""
    validate_object_id(scene_id, "scene_id")
    doc = await get_scene_by_id(db, scene_id)
    if not doc:
        raise_not_found("Scene", scene_id)
    return doc


@router.patch(
    "/{scene_id}",
    response_model=SceneDocument,
    summary="Update audio path and status for a scene",
)
async def update_tts(
    scene_id: str,
    payload: SceneUpdate,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> SceneDocument:
    """
    Manually set audio_path and status on a scene.
    """
    validate_object_id(scene_id, "scene_id")
    doc = await update_scene(db, scene_id, payload)
    if not doc:
        raise_not_found("Scene", scene_id)
    return doc


"""
routers/animation.py
──────────────────────
Triggers the animation agent for a scene, generates Manim code, persists it,
and tracks the asset path / status on the Scene document.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.agents.animation_agent import generate_animation_code
from backend.config import settings
from backend.models.scene import (
    GenerateAnimationRequest,
    GenerateAnimationResponse,
    RenderSceneRequest,
    RenderSceneResponse,
    SceneDocument,
    SceneStatus,
    SceneUpdate,
)
from backend.services.animation_renderer import render_scene
from backend.services.database import db_dependency
from backend.services.scene_service import get_scene_by_id, update_scene
from backend.utils.errors import raise_not_found, validate_object_id

router = APIRouter(tags=["Animation"])

# Directory where generated .py files are stored
_ANIM_DIR = Path(settings.storage_root) / "animations"
_ANIM_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# AI Animation Generation
# ---------------------------------------------------------------------------

@router.post(
    "/generate-animation",
    response_model=GenerateAnimationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a Manim animation script for a scene",
    description=(
        "Fetches the scene, sends its visual description + narration to the LLM, "
        "saves the resulting Manim Python script to storage/animations/, "
        "updates the scene document with the file path, and returns the code."
    ),
)
async def generate_animation_endpoint(
    payload: GenerateAnimationRequest,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> GenerateAnimationResponse:
    validate_object_id(payload.scene_id, "scene_id")

    # 1. Fetch the scene
    scene_doc = await get_scene_by_id(db, payload.scene_id)
    if not scene_doc:
        raise_not_found("Scene", payload.scene_id)

    if not scene_doc.visual_description:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Scene has no visual_description. Run scene planning first "
                   "via POST /api/v1/scene/generate-scenes",
        )

    # 2. Mark as rendering
    await update_scene(db, payload.scene_id, SceneUpdate(status=SceneStatus.RENDERING))

    # 3. Call the LLM agent
    resolved_model = payload.model or settings.openai_model
    scene_dict = {
        "index": scene_doc.index,
        "narration_text": scene_doc.narration_text,
        "visual_description": scene_doc.visual_description,
        "focus_words": scene_doc.focus_words,
    }
    try:
        manim_code = await generate_animation_code(scene_dict, model=payload.model)
    except Exception as exc:
        await update_scene(
            db,
            payload.scene_id,
            SceneUpdate(status=SceneStatus.FAILED, error_message=str(exc)),
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Animation code generation failed: {exc}",
        ) from exc

    # 4. Persist the .py file
    filename = f"scene_{scene_doc.index:03d}_{uuid.uuid4().hex[:8]}.py"
    file_path = _ANIM_DIR / filename
    file_path.write_text(manim_code, encoding="utf-8")
    relative_path = str(file_path.relative_to(Path(".")))

    # 5. Update scene document
    await update_scene(
        db,
        payload.scene_id,
        SceneUpdate(
            status=SceneStatus.READY,
            animation_path=relative_path,
            animation_code=manim_code,
        ),
    )

    return GenerateAnimationResponse(
        scene_id=payload.scene_id,
        animation_path=relative_path,
        model_used=resolved_model,
        manim_code=manim_code,
    )


# ---------------------------------------------------------------------------
# Manim Render
# ---------------------------------------------------------------------------

@router.post(
    "/render-scene",
    response_model=RenderSceneResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Render a scene's Manim code to an MP4 video",
    description=(
        "Runs the Manim CLI on the stored animation_code for the given scene, "
        "saves the output MP4 to storage/videos/, updates the scene document "
        "with the video path, and returns the result. "
        "Requires Manim to be installed: pip install manim"
    ),
)
async def render_scene_endpoint(
    payload: RenderSceneRequest,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> RenderSceneResponse:
    validate_object_id(payload.scene_id, "scene_id")

    # 1. Fetch the scene
    scene_doc = await get_scene_by_id(db, payload.scene_id)
    if not scene_doc:
        raise_not_found("Scene", payload.scene_id)

    if not scene_doc.animation_code:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Scene has no animation_code. Generate animation code first "
                   "via POST /api/v1/animation/generate-animation",
        )

    # 2. Mark as rendering
    await update_scene(db, payload.scene_id, SceneUpdate(status=SceneStatus.RENDERING))

    # 3. Run Manim
    stem = f"scene_{scene_doc.index:03d}_{uuid.uuid4().hex[:8]}"
    try:
        result = await render_scene(
            scene_doc.animation_code,
            stem=stem,
            quality=payload.quality,
        )
        mp4_path = result.path
    except Exception as exc:
        await update_scene(
            db,
            payload.scene_id,
            SceneUpdate(status=SceneStatus.FAILED, error_message=str(exc)),
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Manim render failed: {exc}",
        ) from exc

    # 4. Persist video path on scene
    relative = str(mp4_path.relative_to(Path(".").resolve()))
    await update_scene(
        db,
        payload.scene_id,
        SceneUpdate(
            status=SceneStatus.READY,
            rendered_video_path=relative,
        ),
    )

    return RenderSceneResponse(
        scene_id=payload.scene_id,
        video_path=relative,
        status=SceneStatus.READY,
    )


# ---------------------------------------------------------------------------
# Legacy / status endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/generate/{scene_id}",
    response_model=SceneDocument,
    summary="Mark a scene as rendering (manual trigger)",
)
async def trigger_animation(
    scene_id: str,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> SceneDocument:
    """
    Marks the scene as `rendering`. Use POST /generate-animation for the full
    AI-powered pipeline.
    """
    validate_object_id(scene_id, "scene_id")
    doc = await get_scene_by_id(db, scene_id)
    if not doc:
        raise_not_found("Scene", scene_id)
    return await update_scene(db, scene_id, SceneUpdate(status=SceneStatus.RENDERING))


@router.get(
    "/{scene_id}",
    response_model=SceneDocument,
    summary="Get animation status for a scene",
)
async def get_animation_status(
    scene_id: str,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> SceneDocument:
    """Returns the full scene document including animation_path and status."""
    validate_object_id(scene_id, "scene_id")
    doc = await get_scene_by_id(db, scene_id)
    if not doc:
        raise_not_found("Scene", scene_id)
    return doc


@router.patch(
    "/{scene_id}",
    response_model=SceneDocument,
    summary="Update animation path and status for a scene",
)
async def update_animation(
    scene_id: str,
    payload: SceneUpdate,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> SceneDocument:
    """
    Called by the animation agent once rendering is complete.
    Typically sets `animation_path` and `status = ready`.
    """
    validate_object_id(scene_id, "scene_id")
    doc = await update_scene(db, scene_id, payload)
    if not doc:
        raise_not_found("Scene", scene_id)
    return doc


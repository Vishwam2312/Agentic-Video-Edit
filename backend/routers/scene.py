"""
routers/scene.py
─────────────────
Manages Scene documents — discrete visual segments planned from a Script.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.agents.scene_agent import generate_scenes
from backend.config import settings
from backend.models.scene import (
    GenerateScenesRequest,
    GenerateScenesResponse,
    SceneCreate,
    SceneDocument,
    SceneOut,
    SceneResponse,
    SceneUpdate,
)
from backend.services.database import db_dependency
from backend.services.scene_service import (
    bulk_create_scenes,
    create_scene,
    delete_scene,
    delete_scenes_for_project,
    delete_scenes_for_script,
    get_scene_by_id,
    list_scenes_for_project,
    list_scenes_for_script,
    update_scene,
)
from backend.services.script_service import get_script_by_id
from backend.models.script import ScriptStatus
from backend.utils.errors import raise_not_found, validate_object_id

router = APIRouter(tags=["Scene Planning"])


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=SceneDocument,
    status_code=status.HTTP_201_CREATED,
    summary="Create a single scene",
)
async def create_single_scene(
    payload: SceneCreate,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> SceneDocument:
    validate_object_id(payload.project_id, "project_id")
    validate_object_id(payload.script_id, "script_id")
    return await create_scene(db, payload)


@router.post(
    "/bulk",
    response_model=list[SceneDocument],
    status_code=status.HTTP_201_CREATED,
    summary="Bulk-create scenes for a script",
)
async def create_bulk_scenes(
    payloads: list[SceneCreate],
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> list[SceneDocument]:
    """Insert multiple scenes in a single database round-trip."""
    for p in payloads:
        validate_object_id(p.project_id, "project_id")
        validate_object_id(p.script_id, "script_id")
    return await bulk_create_scenes(db, payloads)


# ---------------------------------------------------------------------------
# Read  (specific paths before generic /{id})
# ---------------------------------------------------------------------------

@router.get(
    "/project/{project_id}",
    response_model=list[SceneResponse],
    summary="List all scenes for a project",
)
async def scenes_for_project(
    project_id: str,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> list[SceneDocument]:
    validate_object_id(project_id, "project_id")
    return await list_scenes_for_project(db, project_id)


@router.get(
    "/script/{script_id}",
    response_model=list[SceneResponse],
    summary="List all scenes for a script",
)
async def scenes_for_script(
    script_id: str,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> list[SceneDocument]:
    validate_object_id(script_id, "script_id")
    return await list_scenes_for_script(db, script_id)


@router.get(
    "/{scene_id}",
    response_model=SceneDocument,
    summary="Get a scene by ID",
)
async def get_scene(
    scene_id: str,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> SceneDocument:
    validate_object_id(scene_id, "scene_id")
    doc = await get_scene_by_id(db, scene_id)
    if not doc:
        raise_not_found("Scene", scene_id)
    return doc


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

@router.patch(
    "/{scene_id}",
    response_model=SceneDocument,
    summary="Update a scene",
)
async def patch_scene(
    scene_id: str,
    payload: SceneUpdate,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> SceneDocument:
    validate_object_id(scene_id, "scene_id")
    doc = await update_scene(db, scene_id, payload)
    if not doc:
        raise_not_found("Scene", scene_id)
    return doc


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

@router.delete(
    "/{scene_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a scene",
)
async def remove_scene(
    scene_id: str,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> Response:
    validate_object_id(scene_id, "scene_id")
    deleted = await delete_scene(db, scene_id)
    if not deleted:
        raise_not_found("Scene", scene_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/project/{project_id}",
    summary="Delete all scenes for a project",
)
async def remove_scenes_for_project(
    project_id: str,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> dict:
    validate_object_id(project_id, "project_id")
    count = await delete_scenes_for_project(db, project_id)
    return {"deleted_count": count}


# ---------------------------------------------------------------------------
# AI Scene Generation
# ---------------------------------------------------------------------------

@router.post(
    "/generate-scenes",
    response_model=GenerateScenesResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate visual scenes from a script using AI",
    description=(
        "Fetches the script for the given project/script IDs, sends its "
        "sections to the LLM, bulk-inserts the resulting scenes into MongoDB, "
        "and returns the full scene list. Existing scenes for this script are "
        "replaced on each call (idempotent re-generation)."
    ),
)
async def generate_scenes_endpoint(
    payload: GenerateScenesRequest,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> GenerateScenesResponse:
    validate_object_id(payload.project_id, "project_id")
    validate_object_id(payload.script_id, "script_id")

    # 1. Fetch the script and verify it is ready
    script_doc = await get_script_by_id(db, payload.script_id)
    if not script_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Script {payload.script_id} not found. "
                   "Generate a script first via POST /api/v1/script/generate-script",
        )
    if script_doc.status != ScriptStatus.READY:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Script is not ready (status='{script_doc.status}'). "
                   "Wait for generation to complete.",
        )

    # Build a plain dict for the agent (matches ScriptResult.to_dict() shape)
    script_dict = {
        "title": script_doc.title or "",
        "sections": [
            {"heading": s.heading, "text": s.text}
            for s in (script_doc.sections or [])
        ],
    }
    if not script_dict["sections"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Script has no sections. Re-generate the script first.",
        )

    # 2. Call the LLM agent
    resolved_model = payload.model or settings.openai_model
    try:
        scene_items = await generate_scenes(script_dict, model=payload.model)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Scene generation failed: {exc}",
        ) from exc

    # 3. Replace existing scenes for this script (idempotent)
    await delete_scenes_for_script(db, payload.script_id)

    # 4. Bulk-insert new scenes
    scene_creates = [
        SceneCreate(
            project_id=payload.project_id,
            script_id=payload.script_id,
            index=item.scene_id - 1,   # convert 1-based to 0-based
            narration_text=item.text,
            visual_description=item.visual_description,
            focus_words=item.focus_words,
        )
        for item in scene_items
    ]
    created = await bulk_create_scenes(db, scene_creates)

    return GenerateScenesResponse(
        project_id=payload.project_id,
        script_id=payload.script_id,
        scene_count=len(created),
        model_used=resolved_model,
        scenes=[
            SceneOut(
                scene_id=str(doc.id),
                index=doc.index,
                narration_text=doc.narration_text,
                visual_description=doc.visual_description or "",
                focus_words=doc.focus_words,
            )
            for doc in created
        ],
    )


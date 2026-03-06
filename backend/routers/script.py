"""
routers/script.py
──────────────────
Manages Script documents — the AI-generated narration text for each project.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.agents.script_agent import generate_script
from backend.config import settings
from backend.models.script import (
    GenerateScriptRequest,
    GenerateScriptResponse,
    ScriptCreate,
    ScriptDocument,
    ScriptResponse,
    ScriptSection,
    ScriptStatus,
    ScriptUpdate,
)
from backend.services.database import db_dependency
from backend.services.document_service import get_document_by_project
from backend.services.script_service import (
    create_script,
    delete_script,
    get_script_by_id,
    get_script_by_project,
    list_scripts,
    update_script,
)
from backend.utils.errors import raise_not_found, validate_object_id

router = APIRouter(tags=["Script Generation"])


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=ScriptDocument,
    status_code=status.HTTP_201_CREATED,
    summary="Create a script record for a project",
)
async def create_script_record(
    payload: ScriptCreate,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> ScriptDocument:
    """
    Creates a script document linked to a project.
    Once created, the AI agent will populate the `content` field.
    """
    validate_object_id(payload.project_id, "project_id")
    return await create_script(db, payload)


# ---------------------------------------------------------------------------
# Read — specific routes first to avoid path conflicts
# ---------------------------------------------------------------------------

@router.get(
    "/project/{project_id}",
    response_model=ScriptResponse,
    summary="Get the script for a project",
)
async def get_script_for_project(
    project_id: str,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> ScriptDocument:
    validate_object_id(project_id, "project_id")
    doc = await get_script_by_project(db, project_id)
    if not doc:
        raise_not_found("Script", f"project:{project_id}")
    return doc


@router.get(
    "/",
    response_model=list[ScriptResponse],
    summary="List all scripts",
)
async def list_all_scripts(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> list[ScriptDocument]:
    return await list_scripts(db, skip=skip, limit=limit)


@router.get(
    "/{script_id}",
    response_model=ScriptDocument,
    summary="Get a script by ID",
)
async def get_script(
    script_id: str,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> ScriptDocument:
    validate_object_id(script_id, "script_id")
    doc = await get_script_by_id(db, script_id)
    if not doc:
        raise_not_found("Script", script_id)
    return doc


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

@router.patch(
    "/{script_id}",
    response_model=ScriptDocument,
    summary="Update script content or status",
)
async def patch_script(
    script_id: str,
    payload: ScriptUpdate,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> ScriptDocument:
    validate_object_id(script_id, "script_id")
    doc = await update_script(db, script_id, payload)
    if not doc:
        raise_not_found("Script", script_id)
    return doc


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

@router.delete(
    "/{script_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a script",
)
async def remove_script(
    script_id: str,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> Response:
    validate_object_id(script_id, "script_id")
    deleted = await delete_script(db, script_id)
    if not deleted:
        raise_not_found("Script", script_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# AI Script Generation
# ---------------------------------------------------------------------------

@router.post(
    "/generate-script",
    response_model=GenerateScriptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate an educational script from a project's parsed document",
    description=(
        "Fetches the parsed PDF text for the given project, sends it to the "
        "configured LLM, stores the structured script in MongoDB, and returns "
        "the result. The `model` field is optional — omit it to use the server "
        "default (`OPENAI_MODEL` env var, e.g. `gpt-4o-mini`)."
    ),
)
async def generate_script_endpoint(
    payload: GenerateScriptRequest,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> GenerateScriptResponse:
    validate_object_id(payload.project_id, "project_id")

    # 1. Fetch the parsed document for this project
    doc = await get_document_by_project(db, payload.project_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No parsed document found for project {payload.project_id}. "
                   "Upload a PDF first via POST /api/v1/upload/",
        )

    # 2. Create a placeholder script record with GENERATING status
    resolved_model = payload.model or settings.openai_model
    script_doc = await create_script(
        db,
        ScriptCreate(project_id=doc.project_id, model_used=resolved_model),
    )
    script_id = str(script_doc.id)

    # 3. Call the LLM agent
    try:
        result = await generate_script(doc.text, model=payload.model)
    except Exception as exc:
        # Persist the failure so callers can inspect it later
        await update_script(
            db,
            script_id,
            ScriptUpdate(
                status=ScriptStatus.FAILED,
                error_message=str(exc),
            ),
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM generation failed: {exc}",
        ) from exc

    # 4. Persist the structured result
    sections_payload = [
        ScriptSection(heading=s.heading, text=s.text) for s in result.sections
    ]
    updated = await update_script(
        db,
        script_id,
        ScriptUpdate(
            status=ScriptStatus.READY,
            title=result.title,
            sections=sections_payload,
            content=result.full_text,
            word_count=result.word_count,
            model_used=resolved_model,
        ),
    )

    return GenerateScriptResponse(
        script_id=script_id,
        project_id=payload.project_id,
        status=ScriptStatus.READY,
        title=updated.title,
        sections=updated.sections or [],
        word_count=updated.word_count or result.word_count,
        model_used=resolved_model,
    )


"""
routers/script_router.py
─────────────────────────
Script CRUD.  Scripts are stored in the `scripts` MongoDB collection.

Routes
------
POST   /scripts                  create a script
GET    /scripts                  list all scripts (paginated, filterable by project_id)
GET    /scripts/{script_id}      get a single script
PUT    /scripts/{script_id}      full update of a script
DELETE /scripts/{script_id}      delete a script
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from backend.services.database import db_dependency
from backend.services.repositories import ScriptRepository, _to_oid as _validate_oid

router = APIRouter(tags=["Scripts"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class ScriptIn(BaseModel):
    """Body accepted for POST and PUT."""
    project_id: str = Field(..., description="ID of the owning project")
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)


class ScriptOut(BaseModel):
    """Outbound script representation."""
    script_id: str
    project_id: str
    title: str
    content: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _repo_error(exc: ValueError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


def _to_out(doc: dict) -> ScriptOut:
    return ScriptOut(
        script_id=str(doc["_id"]),
        project_id=str(doc["project_id"]),
        title=doc["title"],
        content=doc["content"],
        created_at=doc["created_at"],
    )


# ---------------------------------------------------------------------------
# POST /scripts
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=ScriptOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new script",
)
async def create_script(
    payload: ScriptIn,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> ScriptOut:
    """Creates a script record linked to a project and returns it."""
    try:
        doc = await ScriptRepository.create(db, {
            "project_id": payload.project_id,
            "title": payload.title,
            "content": payload.content,
        })
    except ValueError as exc:
        raise _repo_error(exc)
    return _to_out(doc)


# ---------------------------------------------------------------------------
# GET /scripts
# ---------------------------------------------------------------------------

@router.get(
    "/",
    response_model=list[ScriptOut],
    summary="List scripts",
)
async def list_scripts(
    project_id: Optional[str] = Query(
        default=None,
        description="Filter by project_id",
    ),
    skip: int = Query(default=0, ge=0, description="Records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Max records to return"),
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> list[ScriptOut]:
    """Returns scripts ordered newest-first. Pass `project_id` to filter."""
    filt: dict = {}
    if project_id is not None:
        try:
            _validate_oid(project_id, "project_id")
        except ValueError as exc:
            raise _repo_error(exc)
        filt["project_id"] = project_id

    docs = await ScriptRepository.get_all(db, filter=filt, skip=skip, limit=limit)
    return [_to_out(d) for d in docs]


# ---------------------------------------------------------------------------
# GET /scripts/{script_id}
# ---------------------------------------------------------------------------

@router.get(
    "/{script_id}",
    response_model=ScriptOut,
    summary="Get a script by ID",
)
async def get_script(
    script_id: str,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> ScriptOut:
    try:
        doc = await ScriptRepository.get_by_id(db, script_id)
    except ValueError as exc:
        raise _repo_error(exc)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Script '{script_id}' not found.")
    return _to_out(doc)


# ---------------------------------------------------------------------------
# PUT /scripts/{script_id}
# ---------------------------------------------------------------------------

@router.put(
    "/{script_id}",
    response_model=ScriptOut,
    summary="Update a script",
)
async def update_script(
    script_id: str,
    payload: ScriptIn,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> ScriptOut:
    """Replaces project_id, title, and content of an existing script."""
    try:
        doc = await ScriptRepository.update(db, script_id, {
            "project_id": payload.project_id,
            "title": payload.title,
            "content": payload.content,
        })
    except ValueError as exc:
        raise _repo_error(exc)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Script '{script_id}' not found.")
    return _to_out(doc)


# ---------------------------------------------------------------------------
# DELETE /scripts/{script_id}
# ---------------------------------------------------------------------------

@router.delete(
    "/{script_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a script",
)
async def delete_script(
    script_id: str,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> Response:
    try:
        deleted = await ScriptRepository.delete(db, script_id)
    except ValueError as exc:
        raise _repo_error(exc)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Script '{script_id}' not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

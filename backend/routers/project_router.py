"""
routers/project_router.py
──────────────────────────
Full project CRUD.  Projects are stored in the `projects` MongoDB collection.

Routes
------
POST   /projects                  create a project
GET    /projects                  list all projects (paginated)
GET    /projects/{project_id}     get a single project
PUT    /projects/{project_id}     full update of a project
DELETE /projects/{project_id}     delete a project
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from backend.services.database import db_dependency
from backend.services.repositories import ProjectRepository

router = APIRouter(tags=["Projects"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class ProjectIn(BaseModel):
    """Body accepted for POST and PUT."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)


class ProjectOut(BaseModel):
    """Outbound project representation."""
    project_id: str
    title: str
    description: Optional[str] = None
    created_at: datetime

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _repo_error(exc: ValueError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


def _to_out(doc: dict) -> ProjectOut:
    return ProjectOut(
        project_id=str(doc["_id"]),
        title=doc["title"],
        description=doc.get("description"),
        created_at=doc["created_at"],
    )


# ---------------------------------------------------------------------------
# POST /projects
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=ProjectOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
)
async def create_project(
    payload: ProjectIn,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> ProjectOut:
    """Creates a project record and returns it with the generated project_id."""
    doc = await ProjectRepository.create(db, {
        "title": payload.title,
        "description": payload.description,
    })
    return _to_out(doc)


# ---------------------------------------------------------------------------
# GET /projects
# ---------------------------------------------------------------------------

@router.get(
    "/",
    response_model=list[ProjectOut],
    summary="List all projects",
)
async def list_projects(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Max records to return"),
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> list[ProjectOut]:
    """Returns a paginated list of projects ordered newest-first."""
    docs = await ProjectRepository.get_all(db, skip=skip, limit=limit)
    return [_to_out(d) for d in docs]


# ---------------------------------------------------------------------------
# GET /projects/{project_id}
# ---------------------------------------------------------------------------

@router.get(
    "/{project_id}",
    response_model=ProjectOut,
    summary="Get a project by ID",
)
async def get_project(
    project_id: str,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> ProjectOut:
    try:
        doc = await ProjectRepository.get_by_id(db, project_id)
    except ValueError as exc:
        raise _repo_error(exc)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Project '{project_id}' not found.")
    return _to_out(doc)


# ---------------------------------------------------------------------------
# PUT /projects/{project_id}
# ---------------------------------------------------------------------------

@router.put(
    "/{project_id}",
    response_model=ProjectOut,
    summary="Update a project",
)
async def update_project(
    project_id: str,
    payload: ProjectIn,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> ProjectOut:
    """Replaces the title and description fields of an existing project."""
    try:
        doc = await ProjectRepository.update(db, project_id, {
            "title": payload.title,
            "description": payload.description,
        })
    except ValueError as exc:
        raise _repo_error(exc)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Project '{project_id}' not found.")
    return _to_out(doc)


# ---------------------------------------------------------------------------
# DELETE /projects/{project_id}
# ---------------------------------------------------------------------------

@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
)
async def delete_project(
    project_id: str,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> Response:
    try:
        deleted = await ProjectRepository.delete(db, project_id)
    except ValueError as exc:
        raise _repo_error(exc)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Project '{project_id}' not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

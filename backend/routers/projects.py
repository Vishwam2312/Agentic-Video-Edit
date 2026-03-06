"""
routers/projects.py
────────────────────
Project CRUD and parsed-document read endpoints.

Routes
------
GET    /                              list all projects
GET    /{project_id}                  get a project
PATCH  /{project_id}                  update a project
DELETE /{project_id}                  delete a project
GET    /documents/                    list all parsed documents
GET    /documents/{document_id}       get a parsed document
GET    /documents/project/{project_id} get document for a project
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.models.document import UploadResponse
from backend.models.project import ProjectDocument, ProjectResponse, ProjectUpdate
from backend.services.database import db_dependency
from backend.services.document_service import (
    get_document_by_id,
    get_document_by_project,
    list_documents,
)
from backend.services.project_service import (
    delete_project,
    get_project_by_id,
    list_projects,
    update_project,
)
from backend.utils.errors import raise_not_found, validate_object_id

router = APIRouter(tags=["Projects"])


# ---------------------------------------------------------------------------
# Project CRUD
# ---------------------------------------------------------------------------

@router.get(
    "/",
    response_model=list[ProjectResponse],
    summary="List all projects",
)
async def list_all_projects(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> list[ProjectDocument]:
    """Returns a paginated list of projects ordered by creation date (newest first)."""
    return await list_projects(db, skip=skip, limit=limit)


@router.get(
    "/{project_id}",
    response_model=ProjectDocument,
    summary="Get a project by ID",
)
async def get_project(
    project_id: str,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> ProjectDocument:
    validate_object_id(project_id, "project_id")
    doc = await get_project_by_id(db, project_id)
    if not doc:
        raise_not_found("Project", project_id)
    return doc


@router.patch(
    "/{project_id}",
    response_model=ProjectDocument,
    summary="Partially update a project",
)
async def patch_project(
    project_id: str,
    payload: ProjectUpdate,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> ProjectDocument:
    validate_object_id(project_id, "project_id")
    doc = await update_project(db, project_id, payload)
    if not doc:
        raise_not_found("Project", project_id)
    return doc


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
)
async def remove_project(
    project_id: str,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> Response:
    validate_object_id(project_id, "project_id")
    deleted = await delete_project(db, project_id)
    if not deleted:
        raise_not_found("Project", project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Parsed-document read endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/documents/",
    response_model=list[UploadResponse],
    summary="List all parsed documents",
)
async def list_parsed_documents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> list:
    docs = await list_documents(db, skip=skip, limit=limit)
    return [
        UploadResponse(
            document_id=str(d.id),
            project_id=str(d.project_id),
            file_path=d.upload_path,
            original_filename=d.original_filename,
            page_count=d.page_count,
            text_length=d.text_length,
            word_count=d.word_count,
            pdf_title=d.pdf_title,
            pdf_author=d.pdf_author,
        )
        for d in docs
    ]


@router.get(
    "/documents/{document_id}",
    response_model=UploadResponse,
    summary="Get a parsed document by ID",
)
async def get_parsed_document(
    document_id: str,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> UploadResponse:
    validate_object_id(document_id, "document_id")
    d = await get_document_by_id(db, document_id)
    if not d:
        raise_not_found("Document", document_id)
    return UploadResponse(
        document_id=str(d.id),
        project_id=str(d.project_id),
        file_path=d.upload_path,
        original_filename=d.original_filename,
        page_count=d.page_count,
        text_length=d.text_length,
        word_count=d.word_count,
        pdf_title=d.pdf_title,
        pdf_author=d.pdf_author,
    )


@router.get(
    "/documents/project/{project_id}",
    response_model=UploadResponse,
    summary="Get the parsed document for a project",
)
async def get_parsed_document_for_project(
    project_id: str,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> UploadResponse:
    validate_object_id(project_id, "project_id")
    d = await get_document_by_project(db, project_id)
    if not d:
        raise_not_found("Document", f"project:{project_id}")
    return UploadResponse(
        document_id=str(d.id),
        project_id=str(d.project_id),
        file_path=d.upload_path,
        original_filename=d.original_filename,
        page_count=d.page_count,
        text_length=d.text_length,
        word_count=d.word_count,
        pdf_title=d.pdf_title,
        pdf_author=d.pdf_author,
    )

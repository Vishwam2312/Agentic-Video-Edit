"""
routers/upload.py
──────────────────
Handles research-paper PDF uploads, PDF parsing, and project lifecycle management.

Upload flow:
  1. Validate and save the PDF to storage/uploads/.
  2. Create a Project document in MongoDB.
  3. Parse the PDF (text extraction + metadata) using PyMuPDF.
  4. Store the parsed document in the `documents` collection.
  5. Backfill page_count and text_length on the Project.
  6. Return an UploadResponse with document_id and text_length.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.models.document import ParsedDocumentCreate, UploadResponse
from backend.models.project import ProjectCreate, ProjectUpdate
from backend.services.database import db_dependency
from backend.services.document_service import create_document
from backend.services.pdf_parser import parse_pdf
from backend.services.project_service import create_project, update_project
from backend.utils.errors import validate_object_id
from backend.utils.file_utils import save_upload_file

router = APIRouter(tags=["Upload"])


# ---------------------------------------------------------------------------
# POST /upload  —  upload PDF, parse it, persist everything
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a research-paper PDF, parse it, and create a project",
)
async def upload(
    title: str = Form(..., min_length=1, max_length=255),
    description: str | None = Form(default=None),
    file: UploadFile = File(..., description="PDF file, max 50 MB"),
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> UploadResponse:
    """
    **Full upload pipeline in one call:**

    1. Validates & saves the PDF to `storage/uploads/`.
    2. Creates a `Project` record in MongoDB.
    3. Extracts text and metadata from the PDF (PyMuPDF).
    4. Stores extracted content in the `documents` collection.
    5. Updates the project with `page_count` and `text_length`.

    **Returns** `document_id`, `text_length`, and the file path.
    """
    # 1. Save PDF to disk
    upload_path = await save_upload_file(file)
    original_filename = file.filename or "upload.pdf"

    # 2. Create Project
    project = await create_project(
        db,
        ProjectCreate(
            title=title,
            description=description,
            original_filename=original_filename,
            upload_path=upload_path,
        ),
    )

    # 3. Parse PDF
    try:
        parsed = await parse_pdf(Path(upload_path))
    except Exception as exc:
        logger.error("PDF parsing failed for {}: {}", upload_path, exc)
        # Mark project as failed but still return a useful error
        await update_project(db, str(project.id), ProjectUpdate(error_message=str(exc)))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"PDF could not be parsed: {exc}",
        )

    # 4. Persist parsed document
    doc = await create_document(
        db,
        ParsedDocumentCreate(
            project_id=str(project.id),
            original_filename=original_filename,
            upload_path=upload_path,
            text=parsed.text,
            text_length=parsed.text_length,
            page_count=parsed.page_count,
            word_count=parsed.word_count,
            pdf_title=parsed.pdf_title,
            pdf_author=parsed.pdf_author,
            pdf_subject=parsed.pdf_subject,
            pdf_producer=parsed.pdf_producer,
        ),
    )

    # 5. Backfill project with parsed metadata
    await update_project(
        db,
        str(project.id),
        ProjectUpdate(
            page_count=parsed.page_count,
            text_length=parsed.text_length,
        ),
    )

    logger.info(
        "Upload complete — project_id={} document_id={} pages={} chars={}",
        project.id, doc.id, parsed.page_count, parsed.text_length,
    )

    return UploadResponse(
        document_id=str(doc.id),
        project_id=str(project.id),
        file_path=upload_path,
        original_filename=original_filename,
        page_count=parsed.page_count,
        text_length=parsed.text_length,
        word_count=parsed.word_count,
        pdf_title=parsed.pdf_title,
        pdf_author=parsed.pdf_author,
    )


# ---------------------------------------------------------------------------
# Keep the legacy /paper endpoint as an alias for backwards compat
# ---------------------------------------------------------------------------

@router.post(
    "/paper",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Alias for POST /upload — kept for backwards compatibility",
    include_in_schema=False,
)
async def upload_paper(
    title: str = Form(..., min_length=1, max_length=255),
    description: str | None = Form(default=None),
    file: UploadFile = File(..., description="PDF file, max 50 MB"),
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> UploadResponse:
    return await upload(title=title, description=description, file=file, db=db)


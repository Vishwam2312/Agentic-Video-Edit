"""
services/document_service.py
─────────────────────────────
Async CRUD operations for the `documents` MongoDB collection.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.models.document import ParsedDocumentCreate, ParsedDocumentDocument
from backend.services.database import Collections


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

async def create_document(
    db: AsyncIOMotorDatabase,
    payload: ParsedDocumentCreate,
) -> ParsedDocumentDocument:
    """Insert a new parsed-document record and return it with its generated id."""
    doc = payload.model_dump(by_alias=True, exclude={"id"})
    doc["created_at"] = doc["updated_at"] = datetime.now(timezone.utc)
    result = await db[Collections.DOCUMENTS].insert_one(doc)
    doc["_id"] = result.inserted_id
    return ParsedDocumentDocument.model_validate(doc)


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

async def get_document_by_id(
    db: AsyncIOMotorDatabase,
    document_id: str,
) -> Optional[ParsedDocumentDocument]:
    raw = await db[Collections.DOCUMENTS].find_one({"_id": ObjectId(document_id)})
    return ParsedDocumentDocument.model_validate(raw) if raw else None


async def get_document_by_project(
    db: AsyncIOMotorDatabase,
    project_id: str,
) -> Optional[ParsedDocumentDocument]:
    """Return the parsed document linked to a given project."""
    raw = await db[Collections.DOCUMENTS].find_one(
        {"project_id": ObjectId(project_id)}
    )
    return ParsedDocumentDocument.model_validate(raw) if raw else None


async def list_documents(
    db: AsyncIOMotorDatabase,
    skip: int = 0,
    limit: int = 20,
) -> list[ParsedDocumentDocument]:
    cursor = (
        db[Collections.DOCUMENTS]
        .find()
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    return [ParsedDocumentDocument.model_validate(d) async for d in cursor]


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

async def delete_document(
    db: AsyncIOMotorDatabase,
    document_id: str,
) -> bool:
    result = await db[Collections.DOCUMENTS].delete_one(
        {"_id": ObjectId(document_id)}
    )
    return result.deleted_count == 1


async def delete_document_by_project(
    db: AsyncIOMotorDatabase,
    project_id: str,
) -> bool:
    result = await db[Collections.DOCUMENTS].delete_one(
        {"project_id": ObjectId(project_id)}
    )
    return result.deleted_count == 1

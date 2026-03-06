"""
services/project_service.py
────────────────────────────
Async CRUD operations for the `projects` MongoDB collection.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.models.project import (
    ProjectCreate,
    ProjectDocument,
    ProjectUpdate,
)
from backend.services.database import Collections


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

async def create_project(
    db: AsyncIOMotorDatabase,
    payload: ProjectCreate,
) -> ProjectDocument:
    """Insert a new project document and return it with the generated id."""
    doc = payload.model_dump(by_alias=True, exclude={"id"})
    doc["created_at"] = doc["updated_at"] = datetime.now(timezone.utc)
    result = await db[Collections.PROJECTS].insert_one(doc)
    doc["_id"] = result.inserted_id
    return ProjectDocument.model_validate(doc)


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

async def get_project_by_id(
    db: AsyncIOMotorDatabase,
    project_id: str,
) -> Optional[ProjectDocument]:
    """Return a single project by its ObjectId string, or None if not found."""
    raw = await db[Collections.PROJECTS].find_one(
        {"_id": ObjectId(project_id)}
    )
    return ProjectDocument.model_validate(raw) if raw else None


async def list_projects(
    db: AsyncIOMotorDatabase,
    skip: int = 0,
    limit: int = 20,
) -> list[ProjectDocument]:
    """Return a paginated list of all projects, newest first."""
    cursor = (
        db[Collections.PROJECTS]
        .find()
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    return [ProjectDocument.model_validate(doc) async for doc in cursor]


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

async def update_project(
    db: AsyncIOMotorDatabase,
    project_id: str,
    payload: ProjectUpdate,
) -> Optional[ProjectDocument]:
    """Apply a partial update and return the refreshed document."""
    updates = payload.model_dump(exclude_none=True, by_alias=True, exclude={"id"})
    if not updates:
        return await get_project_by_id(db, project_id)

    updates["updated_at"] = datetime.now(timezone.utc)
    await db[Collections.PROJECTS].update_one(
        {"_id": ObjectId(project_id)},
        {"$set": updates},
    )
    return await get_project_by_id(db, project_id)


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

async def delete_project(
    db: AsyncIOMotorDatabase,
    project_id: str,
) -> bool:
    """Delete a project by id. Returns True if a document was deleted."""
    result = await db[Collections.PROJECTS].delete_one(
        {"_id": ObjectId(project_id)}
    )
    return result.deleted_count == 1

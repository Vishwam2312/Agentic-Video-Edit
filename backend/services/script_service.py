"""
services/script_service.py
───────────────────────────
Async CRUD operations for the `scripts` MongoDB collection.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.models.script import ScriptCreate, ScriptDocument, ScriptUpdate
from backend.services.database import Collections


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

async def create_script(
    db: AsyncIOMotorDatabase,
    payload: ScriptCreate,
) -> ScriptDocument:
    doc = payload.model_dump(by_alias=True, exclude={"id"})
    doc["created_at"] = doc["updated_at"] = datetime.now(timezone.utc)
    result = await db[Collections.SCRIPTS].insert_one(doc)
    doc["_id"] = result.inserted_id
    return ScriptDocument.model_validate(doc)


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

async def get_script_by_id(
    db: AsyncIOMotorDatabase,
    script_id: str,
) -> Optional[ScriptDocument]:
    raw = await db[Collections.SCRIPTS].find_one({"_id": ObjectId(script_id)})
    return ScriptDocument.model_validate(raw) if raw else None


async def get_script_by_project(
    db: AsyncIOMotorDatabase,
    project_id: str,
) -> Optional[ScriptDocument]:
    """Return the script associated with a given project."""
    raw = await db[Collections.SCRIPTS].find_one(
        {"project_id": ObjectId(project_id)}
    )
    return ScriptDocument.model_validate(raw) if raw else None


async def list_scripts(
    db: AsyncIOMotorDatabase,
    skip: int = 0,
    limit: int = 20,
) -> list[ScriptDocument]:
    cursor = (
        db[Collections.SCRIPTS]
        .find()
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    return [ScriptDocument.model_validate(doc) async for doc in cursor]


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

async def update_script(
    db: AsyncIOMotorDatabase,
    script_id: str,
    payload: ScriptUpdate,
) -> Optional[ScriptDocument]:
    updates = payload.model_dump(exclude_none=True, by_alias=True, exclude={"id"})
    if not updates:
        return await get_script_by_id(db, script_id)

    updates["updated_at"] = datetime.now(timezone.utc)
    await db[Collections.SCRIPTS].update_one(
        {"_id": ObjectId(script_id)},
        {"$set": updates},
    )
    return await get_script_by_id(db, script_id)


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

async def delete_script(
    db: AsyncIOMotorDatabase,
    script_id: str,
) -> bool:
    result = await db[Collections.SCRIPTS].delete_one(
        {"_id": ObjectId(script_id)}
    )
    return result.deleted_count == 1

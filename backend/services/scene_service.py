"""
services/scene_service.py
──────────────────────────
Async CRUD operations for the `scenes` MongoDB collection.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.models.scene import SceneCreate, SceneDocument, SceneUpdate
from backend.services.database import Collections


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

async def create_scene(
    db: AsyncIOMotorDatabase,
    payload: SceneCreate,
) -> SceneDocument:
    doc = payload.model_dump(by_alias=True, exclude={"id"})
    doc["created_at"] = doc["updated_at"] = datetime.now(timezone.utc)
    result = await db[Collections.SCENES].insert_one(doc)
    doc["_id"] = result.inserted_id
    return SceneDocument.model_validate(doc)


async def bulk_create_scenes(
    db: AsyncIOMotorDatabase,
    payloads: list[SceneCreate],
) -> list[SceneDocument]:
    """Insert multiple scenes in a single round-trip."""
    now = datetime.now(timezone.utc)
    docs = [
        {**p.model_dump(by_alias=True, exclude={"id"}), "created_at": now, "updated_at": now}
        for p in payloads
    ]
    result = await db[Collections.SCENES].insert_many(docs)
    for doc, inserted_id in zip(docs, result.inserted_ids):
        doc["_id"] = inserted_id
    return [SceneDocument.model_validate(d) for d in docs]


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

async def get_scene_by_id(
    db: AsyncIOMotorDatabase,
    scene_id: str,
) -> Optional[SceneDocument]:
    raw = await db[Collections.SCENES].find_one({"_id": ObjectId(scene_id)})
    return SceneDocument.model_validate(raw) if raw else None


async def list_scenes_for_project(
    db: AsyncIOMotorDatabase,
    project_id: str,
) -> list[SceneDocument]:
    """Return all scenes for a project, ordered by scene index."""
    cursor = (
        db[Collections.SCENES]
        .find({"project_id": ObjectId(project_id)})
        .sort("index", 1)
    )
    return [SceneDocument.model_validate(doc) async for doc in cursor]


async def list_scenes_for_script(
    db: AsyncIOMotorDatabase,
    script_id: str,
) -> list[SceneDocument]:
    cursor = (
        db[Collections.SCENES]
        .find({"script_id": ObjectId(script_id)})
        .sort("index", 1)
    )
    return [SceneDocument.model_validate(doc) async for doc in cursor]


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

async def update_scene(
    db: AsyncIOMotorDatabase,
    scene_id: str,
    payload: SceneUpdate,
) -> Optional[SceneDocument]:
    updates = payload.model_dump(exclude_none=True, by_alias=True, exclude={"id"})
    if not updates:
        return await get_scene_by_id(db, scene_id)

    updates["updated_at"] = datetime.now(timezone.utc)
    await db[Collections.SCENES].update_one(
        {"_id": ObjectId(scene_id)},
        {"$set": updates},
    )
    return await get_scene_by_id(db, scene_id)


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

async def delete_scene(
    db: AsyncIOMotorDatabase,
    scene_id: str,
) -> bool:
    result = await db[Collections.SCENES].delete_one({"_id": ObjectId(scene_id)})
    return result.deleted_count == 1


async def delete_scenes_for_project(
    db: AsyncIOMotorDatabase,
    project_id: str,
) -> int:
    """Delete all scenes belonging to a project. Returns the count deleted."""
    result = await db[Collections.SCENES].delete_many(
        {"project_id": ObjectId(project_id)}
    )
    return result.deleted_count


async def delete_scenes_for_script(
    db: AsyncIOMotorDatabase,
    script_id: str,
) -> int:
    """Delete all scenes belonging to a script. Returns the count deleted."""
    result = await db[Collections.SCENES].delete_many(
        {"script_id": ObjectId(script_id)}
    )
    return result.deleted_count

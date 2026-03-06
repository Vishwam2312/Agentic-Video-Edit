"""
services/video_service.py
──────────────────────────
Async CRUD operations for the `videos` MongoDB collection.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.models.video import VideoCreate, VideoDocument, VideoUpdate
from backend.services.database import Collections


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

async def create_video(
    db: AsyncIOMotorDatabase,
    payload: VideoCreate,
) -> VideoDocument:
    doc = payload.model_dump(by_alias=True, exclude={"id"})
    doc["created_at"] = doc["updated_at"] = datetime.now(timezone.utc)
    result = await db[Collections.VIDEOS].insert_one(doc)
    doc["_id"] = result.inserted_id
    return VideoDocument.model_validate(doc)


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

async def get_video_by_id(
    db: AsyncIOMotorDatabase,
    video_id: str,
) -> Optional[VideoDocument]:
    raw = await db[Collections.VIDEOS].find_one({"_id": ObjectId(video_id)})
    return VideoDocument.model_validate(raw) if raw else None


async def get_video_by_project(
    db: AsyncIOMotorDatabase,
    project_id: str,
) -> Optional[VideoDocument]:
    """Return the final video record for a given project."""
    raw = await db[Collections.VIDEOS].find_one(
        {"project_id": ObjectId(project_id)}
    )
    return VideoDocument.model_validate(raw) if raw else None


async def list_videos(
    db: AsyncIOMotorDatabase,
    skip: int = 0,
    limit: int = 20,
) -> list[VideoDocument]:
    cursor = (
        db[Collections.VIDEOS]
        .find()
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    return [VideoDocument.model_validate(doc) async for doc in cursor]


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

async def update_video(
    db: AsyncIOMotorDatabase,
    video_id: str,
    payload: VideoUpdate,
) -> Optional[VideoDocument]:
    updates = payload.model_dump(exclude_none=True, by_alias=True, exclude={"id"})
    if not updates:
        return await get_video_by_id(db, video_id)

    updates["updated_at"] = datetime.now(timezone.utc)
    await db[Collections.VIDEOS].update_one(
        {"_id": ObjectId(video_id)},
        {"$set": updates},
    )
    return await get_video_by_id(db, video_id)


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

async def delete_video(
    db: AsyncIOMotorDatabase,
    video_id: str,
) -> bool:
    result = await db[Collections.VIDEOS].delete_one({"_id": ObjectId(video_id)})
    return result.deleted_count == 1

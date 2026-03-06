"""
services/database.py
────────────────────
Motor (async MongoDB) client lifecycle, database accessor,
FastAPI dependency injection, and scene/subscene CRUD helpers.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Optional

import certifi
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from backend.config import settings

# ---------------------------------------------------------------------------
# Module-level client — initialised during app startup, closed on shutdown
# ---------------------------------------------------------------------------

_client: AsyncIOMotorClient | None = None


# ---------------------------------------------------------------------------
# Lifecycle helpers  (called from main.py lifespan)
# ---------------------------------------------------------------------------

async def connect_db() -> None:
    """Open the Motor client and attempt to verify connectivity.

    A failed ping is logged as a warning rather than crashing startup,
    so the server stays available even when MongoDB is temporarily
    unreachable (e.g. during local dev without a running instance).
    """
    global _client
    logger.info("Connecting to MongoDB at {}", settings.mongo_uri)

    # Use certifi's CA bundle so Atlas TLS works on all platforms (Windows/Linux/macOS)
    _client = AsyncIOMotorClient(
        settings.mongo_uri,
        serverSelectionTimeoutMS=15_000,
        connectTimeoutMS=20_000,
        uuidRepresentation="standard",
        tlsCAFile=certifi.where(),
    )
    try:
        await _client.admin.command("ping")
        logger.info("MongoDB connected — database: '{}'", settings.database_name)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "MongoDB ping failed ({}). Running without database — "
            "endpoints that require DB will return 503.",
            exc,
        )


async def disconnect_db() -> None:
    """Close the Motor client gracefully."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("MongoDB connection closed.")


# ---------------------------------------------------------------------------
# Accessors
# ---------------------------------------------------------------------------

def get_client() -> AsyncIOMotorClient:
    if _client is None:
        raise RuntimeError(
            "MongoDB client is not initialised. "
            "Ensure connect_db() has been awaited during app startup."
        )
    return _client


def get_database() -> AsyncIOMotorDatabase:
    return get_client()[settings.database_name]


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

async def db_dependency() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """
    Yields the Motor database instance as a FastAPI dependency.

    Usage in a router:
        from fastapi import Depends
        from motor.motor_asyncio import AsyncIOMotorDatabase
        from backend.services.database import db_dependency

        @router.get("/example")
        async def example(db: AsyncIOMotorDatabase = Depends(db_dependency)):
            doc = await db["collection"].find_one({})
            ...
    """
    yield get_database()


# ---------------------------------------------------------------------------
# Collection helpers — centralised collection names
# ---------------------------------------------------------------------------

class Collections:
    PROJECTS   = "projects"
    SCRIPTS    = "scripts"
    SCENES     = "scenes"
    VIDEOS     = "videos"
    DOCUMENTS  = "documents"
    HIGHLIGHTS = "highlights"


# ---------------------------------------------------------------------------
# Scene helpers
# ---------------------------------------------------------------------------

async def create_scene(
    scene_id: str,
    scene_title: str,
    project_id: str,
    subscenes: Optional[list[dict]] = None,
    *,
    db: Optional[AsyncIOMotorDatabase] = None,
) -> dict:
    """
    Insert a new scene document into the ``scenes`` collection.

    The document uses ``scene_id`` as its ``_id`` so callers control the
    identifier (UUID hex or any unique string).

    Parameters
    ----------
    scene_id:
        Unique identifier used as ``_id`` in MongoDB.
    scene_title:
        Human-readable title for the scene.
    project_id:
        The parent project this scene belongs to.
    subscenes:
        Optional list of pre-serialised subscene dicts to embed at creation.
    db:
        Motor database instance. Falls back to ``get_database()`` when omitted
        (convenient for direct calls outside of a request context).

    Returns
    -------
    dict
        The inserted document as stored in MongoDB.

    Raises
    ------
    ValueError
        If a scene with the same ``scene_id`` already exists.
    """
    _db = db or get_database()
    now = datetime.now(tz=timezone.utc)
    doc: dict[str, Any] = {
        "_id": scene_id,
        "scene_title": scene_title,
        "project_id": project_id,
        "subscenes": subscenes or [],
        "created_at": now,
        "updated_at": now,
    }
    try:
        await _db[Collections.SCENES].insert_one(doc)
    except DuplicateKeyError as exc:
        raise ValueError(
            f"A scene with scene_id '{scene_id}' already exists."
        ) from exc
    logger.debug("create_scene — inserted scene_id={}", scene_id)
    return doc


async def get_scene(
    scene_id: str,
    *,
    db: Optional[AsyncIOMotorDatabase] = None,
) -> Optional[dict]:
    """
    Fetch a single scene document by its ``scene_id`` (``_id``).

    Returns ``None`` if no matching document exists.
    """
    _db = db or get_database()
    return await _db[Collections.SCENES].find_one({"_id": scene_id})


async def append_subscene(
    scene_id: str,
    subscene: dict,
    *,
    db: Optional[AsyncIOMotorDatabase] = None,
) -> Optional[dict]:
    """
    Append a single subscene dict to a scene's ``subscenes`` array using
    MongoDB's ``$push`` operator (atomic, no read-modify-write).

    Also updates ``updated_at`` on the parent scene.

    Parameters
    ----------
    scene_id:
        The ``_id`` of the target scene.
    subscene:
        Fully serialised subscene dict. Must contain at least
        ``subscene_id``, ``text``, ``visual_description``, and ``video_ids``.
        A ``created_at`` timestamp is injected automatically if absent.

    Returns
    -------
    dict | None
        The updated scene document, or ``None`` if ``scene_id`` was not found.
    """
    _db = db or get_database()
    if "created_at" not in subscene:
        subscene = {**subscene, "created_at": datetime.now(tz=timezone.utc)}

    doc = await _db[Collections.SCENES].find_one_and_update(
        {"_id": scene_id},
        {
            "$push": {"subscenes": subscene},
            "$set": {"updated_at": datetime.now(tz=timezone.utc)},
        },
        return_document=ReturnDocument.AFTER,
    )
    if doc is None:
        logger.warning("append_subscene — scene_id={} not found", scene_id)
    else:
        logger.debug(
            "append_subscene — scene_id={} now has {} subscene(s)",
            scene_id,
            len(doc.get("subscenes", [])),
        )
    return doc


async def update_subscene(
    scene_id: str,
    subscene_id: str,
    updates: dict,
    *,
    db: Optional[AsyncIOMotorDatabase] = None,
) -> Optional[dict]:
    """
    Partially update fields on an existing subscene using the array
    positional operator (``subscenes.$``).

    Only the keys present in ``updates`` are changed; other fields are
    left untouched.

    Parameters
    ----------
    scene_id:
        The ``_id`` of the parent scene.
    subscene_id:
        The ``subscene_id`` of the subscene to update.
    updates:
        Dict of field → new value. Keys must be valid subscene field names
        (``text``, ``visual_description``, ``video_ids``, ``metadata``).

    Returns
    -------
    dict | None
        The updated scene document, or ``None`` if no match was found.
    """
    _db = db or get_database()
    # Build a $set payload that targets only the matched array element
    set_fields: dict[str, Any] = {
        f"subscenes.$.{key}": value for key, value in updates.items()
    }
    set_fields["updated_at"] = datetime.now(tz=timezone.utc)

    doc = await _db[Collections.SCENES].find_one_and_update(
        {"_id": scene_id, "subscenes.subscene_id": subscene_id},
        {"$set": set_fields},
        return_document=ReturnDocument.AFTER,
    )
    if doc is None:
        logger.warning(
            "update_subscene — scene_id={} or subscene_id={} not found",
            scene_id,
            subscene_id,
        )
    else:
        logger.debug(
            "update_subscene — scene_id={} subscene_id={} updated fields={}",
            scene_id,
            subscene_id,
            list(updates.keys()),
        )
    return doc


async def add_video_to_subscene(
    scene_id: str,
    subscene_id: str,
    video_id: str,
    *,
    db: Optional[AsyncIOMotorDatabase] = None,
) -> Optional[dict]:
    """
    Append a single ``video_id`` to a subscene's ``video_ids`` array using
    ``$push``, avoiding duplicate entries via ``$addToSet``.

    Parameters
    ----------
    scene_id:
        The ``_id`` of the parent scene.
    subscene_id:
        The ``subscene_id`` of the target subscene.
    video_id:
        The video chunk ID to add.

    Returns
    -------
    dict | None
        The updated scene document, or ``None`` if no match was found.
    """
    _db = db or get_database()
    doc = await _db[Collections.SCENES].find_one_and_update(
        {"_id": scene_id, "subscenes.subscene_id": subscene_id},
        {
            "$addToSet": {"subscenes.$.video_ids": video_id},
            "$set": {"updated_at": datetime.now(tz=timezone.utc)},
        },
        return_document=ReturnDocument.AFTER,
    )
    if doc is None:
        logger.warning(
            "add_video_to_subscene — scene_id={} or subscene_id={} not found",
            scene_id,
            subscene_id,
        )
    else:
        logger.debug(
            "add_video_to_subscene — scene_id={} subscene_id={} video_id={}",
            scene_id,
            subscene_id,
            video_id,
        )
    return doc

"""
services/repositories.py
─────────────────────────
MongoDB abstraction layer.

Each repository class wraps one collection and exposes five async methods:

    create(db, data)          → dict
    get_by_id(db, id)         → dict | None
    get_all(db, *, filter, skip, limit, sort_field, sort_dir)  → list[dict]
    update(db, id, updates)   → dict | None
    delete(db, id)            → bool

All methods accept an ``AsyncIOMotorDatabase`` as their first argument so
they stay stateless and work cleanly with FastAPI's ``db_dependency``
injection.

Example usage
-------------
    from backend.services.repositories import ScriptRepository

    # inside a FastAPI route handler:
    doc = await ScriptRepository.create(db, {"project_id": ..., "title": ..., "content": ...})
    doc = await ScriptRepository.get_by_id(db, script_id)
    docs = await ScriptRepository.get_all(db, filter={"project_id": pid})
    doc = await ScriptRepository.update(db, script_id, {"title": "New title"})
    deleted = await ScriptRepository.delete(db, script_id)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.services.database import Collections


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _to_oid(value: str, field: str = "id") -> ObjectId:
    """Convert a hex string to ObjectId, raising ValueError on bad input."""
    try:
        return ObjectId(value)
    except (InvalidId, Exception) as exc:
        raise ValueError(f"'{value}' is not a valid {field}.") from exc


def _serialize(doc: dict) -> dict:
    """Replace ``_id`` ObjectId with a plain ``str`` in place and return the doc."""
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


# ---------------------------------------------------------------------------
# Base repository
# ---------------------------------------------------------------------------

class BaseRepository:
    """
    Generic async repository for a single MongoDB collection.

    Subclass and override ``collection`` to specialise.
    All methods are ``@classmethod`` so no instantiation is needed.
    """

    collection: str  # must be set by each subclass

    # ── Create ───────────────────────────────────────────────────────────────

    @classmethod
    async def create(
        cls,
        db: AsyncIOMotorDatabase,
        data: dict[str, Any],
    ) -> dict:
        """
        Insert *data* into the collection, automatically adding
        ``created_at`` and ``updated_at`` timestamps.

        Returns the inserted document with ``_id`` as a string.
        """
        now = datetime.now(timezone.utc)
        doc = {**data, "created_at": now, "updated_at": now}
        result = await db[cls.collection].insert_one(doc)
        doc["_id"] = result.inserted_id
        return _serialize(doc)

    # ── Get by ID ─────────────────────────────────────────────────────────────

    @classmethod
    async def get_by_id(
        cls,
        db: AsyncIOMotorDatabase,
        record_id: str,
    ) -> Optional[dict]:
        """
        Fetch a single document by its ObjectId string.

        Returns ``None`` if no document matches.
        Raises ``ValueError`` if *record_id* is not a valid ObjectId.
        """
        doc = await db[cls.collection].find_one({"_id": _to_oid(record_id)})
        return _serialize(doc) if doc else None

    # ── Get all ───────────────────────────────────────────────────────────────

    @classmethod
    async def get_all(
        cls,
        db: AsyncIOMotorDatabase,
        *,
        filter: Optional[dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 20,
        sort_field: str = "created_at",
        sort_dir: int = -1,  # -1 = descending (newest first)
    ) -> list[dict]:
        """
        Return a paginated list of documents.

        Parameters
        ----------
        filter:
            Optional MongoDB filter dict (e.g. ``{"project_id": "abc"}``).
        skip / limit:
            Standard pagination controls.
        sort_field / sort_dir:
            Field to sort on and direction (1 = asc, -1 = desc).
        """
        query = filter or {}
        cursor = (
            db[cls.collection]
            .find(query)
            .sort(sort_field, sort_dir)
            .skip(skip)
            .limit(limit)
        )
        return [_serialize(doc) async for doc in cursor]

    # ── Update ────────────────────────────────────────────────────────────────

    @classmethod
    async def update(
        cls,
        db: AsyncIOMotorDatabase,
        record_id: str,
        updates: dict[str, Any],
    ) -> Optional[dict]:
        """
        Apply a ``$set`` patch to the document identified by *record_id*.

        ``updated_at`` is always refreshed automatically.
        Returns the post-update document, or ``None`` if not found.
        Raises ``ValueError`` if *record_id* is not a valid ObjectId.
        """
        payload = {**updates, "updated_at": datetime.now(timezone.utc)}
        result = await db[cls.collection].update_one(
            {"_id": _to_oid(record_id)},
            {"$set": payload},
        )
        if result.matched_count == 0:
            return None
        return await cls.get_by_id(db, record_id)

    # ── Delete ────────────────────────────────────────────────────────────────

    @classmethod
    async def delete(
        cls,
        db: AsyncIOMotorDatabase,
        record_id: str,
    ) -> bool:
        """
        Delete the document identified by *record_id*.

        Returns ``True`` if a document was deleted, ``False`` otherwise.
        Raises ``ValueError`` if *record_id* is not a valid ObjectId.
        """
        result = await db[cls.collection].delete_one({"_id": _to_oid(record_id)})
        return result.deleted_count == 1


# ---------------------------------------------------------------------------
# Concrete repositories
# ---------------------------------------------------------------------------

class ProjectRepository(BaseRepository):
    """Repository for the ``projects`` collection."""
    collection = Collections.PROJECTS


class ScriptRepository(BaseRepository):
    """
    Repository for the ``scripts`` collection.

    Scripts use a UUID string as their domain key (``script_id`` field),
    stored alongside the MongoDB ``_id``.  The five script-specific helpers
    below operate on ``script_id``; the inherited base methods still work
    via MongoDB ``_id`` for generic access.
    """

    collection = Collections.SCRIPTS

    # ── Script-specific helpers ───────────────────────────────────────────────

    @classmethod
    async def create_script(
        cls,
        db: AsyncIOMotorDatabase,
        script_data: dict[str, Any],
    ) -> dict:
        """
        Create a new script document.

        A UUID ``script_id`` is generated automatically if not present in
        *script_data*.  Required keys: ``project_id``, ``title``, ``content``.
        The document shape is::

            {
                "script_id":  "<uuid-hex>",
                "project_id": "<string>",
                "title":      "<string>",
                "content":    "<string>",
                "created_at": <datetime>,
                "updated_at": <datetime>,
            }

        Returns the inserted document with ``_id`` serialised to a string.
        """
        now = datetime.now(timezone.utc)
        doc = {
            "script_id": uuid.uuid4().hex,
            **script_data,
            "created_at": now,
            "updated_at": now,
        }
        result = await db[cls.collection].insert_one(doc)
        doc["_id"] = result.inserted_id
        return _serialize(doc)

    @classmethod
    async def get_script(
        cls,
        db: AsyncIOMotorDatabase,
        script_id: str,
    ) -> Optional[dict]:
        """
        Fetch a script by its UUID ``script_id``.

        Returns ``None`` if no document matches.
        """
        doc = await db[cls.collection].find_one({"script_id": script_id})
        return _serialize(doc) if doc else None

    @classmethod
    async def get_scripts_by_project(
        cls,
        db: AsyncIOMotorDatabase,
        project_id: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[dict]:
        """
        Return all scripts belonging to *project_id*, ordered newest-first.
        """
        cursor = (
            db[cls.collection]
            .find({"project_id": project_id})
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )
        return [_serialize(doc) async for doc in cursor]

    @classmethod
    async def update_script(
        cls,
        db: AsyncIOMotorDatabase,
        script_id: str,
        update_data: dict[str, Any],
    ) -> Optional[dict]:
        """
        Apply a ``$set`` patch to the script identified by *script_id*.

        ``updated_at`` is refreshed automatically.
        Returns the post-update document, or ``None`` if not found.
        """
        payload = {**update_data, "updated_at": datetime.now(timezone.utc)}
        result = await db[cls.collection].update_one(
            {"script_id": script_id},
            {"$set": payload},
        )
        if result.matched_count == 0:
            return None
        return await cls.get_script(db, script_id)

    @classmethod
    async def delete_script(
        cls,
        db: AsyncIOMotorDatabase,
        script_id: str,
    ) -> bool:
        """
        Delete the script identified by *script_id*.

        Returns ``True`` if a document was deleted, ``False`` otherwise.
        """
        result = await db[cls.collection].delete_one({"script_id": script_id})
        return result.deleted_count == 1


class SceneRepository(BaseRepository):
    """
    Repository for the ``scenes`` collection.

    Scenes use a UUID string as their primary key (``scene_id`` field),
    stored alongside the MongoDB ``_id``.  The five scene-specific helpers
    below operate on ``scene_id``; the inherited base methods still work
    via MongoDB ``_id`` for generic access.
    """

    collection = Collections.SCENES

    # ── Scene-specific helpers ────────────────────────────────────────────────

    @classmethod
    async def create_scene(
        cls,
        db: AsyncIOMotorDatabase,
        project_id: str,
        scene_title: str,
    ) -> dict:
        """
        Create a new scene document.

        A UUID ``scene_id`` is generated automatically.  The document shape is::

            {
                "scene_id":   "<uuid-hex>",
                "project_id": "<string>",
                "scene_title": "<string>",
                "subscenes":  [],
                "created_at": <datetime>,
                "updated_at": <datetime>,
            }

        Returns the inserted document with ``_id`` serialised to a string.
        """
        scene_id = uuid.uuid4().hex
        now = datetime.now(timezone.utc)
        doc = {
            "scene_id": scene_id,
            "project_id": project_id,
            "scene_title": scene_title,
            "subscenes": [],
            "created_at": now,
            "updated_at": now,
        }
        result = await db[cls.collection].insert_one(doc)
        doc["_id"] = result.inserted_id
        return _serialize(doc)

    @classmethod
    async def get_scene(
        cls,
        db: AsyncIOMotorDatabase,
        scene_id: str,
    ) -> Optional[dict]:
        """
        Fetch a scene by its UUID ``scene_id``.

        Returns ``None`` if no document matches.
        """
        doc = await db[cls.collection].find_one({"scene_id": scene_id})
        return _serialize(doc) if doc else None

    @classmethod
    async def get_scenes_by_project(
        cls,
        db: AsyncIOMotorDatabase,
        project_id: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[dict]:
        """
        Return all scenes belonging to *project_id*, ordered by creation time
        (oldest first, so scene order is preserved).
        """
        cursor = (
            db[cls.collection]
            .find({"project_id": project_id})
            .sort("created_at", 1)
            .skip(skip)
            .limit(limit)
        )
        return [_serialize(doc) async for doc in cursor]

    @classmethod
    async def update_scene(
        cls,
        db: AsyncIOMotorDatabase,
        scene_id: str,
        update_data: dict[str, Any],
    ) -> Optional[dict]:
        """
        Apply a ``$set`` patch to the scene identified by *scene_id*.

        ``updated_at`` is refreshed automatically.
        Returns the post-update document, or ``None`` if not found.
        """
        payload = {**update_data, "updated_at": datetime.now(timezone.utc)}
        result = await db[cls.collection].update_one(
            {"scene_id": scene_id},
            {"$set": payload},
        )
        if result.matched_count == 0:
            return None
        return await cls.get_scene(db, scene_id)

    @classmethod
    async def delete_scene(
        cls,
        db: AsyncIOMotorDatabase,
        scene_id: str,
    ) -> bool:
        """
        Delete the scene identified by *scene_id*.

        Returns ``True`` if a document was deleted, ``False`` otherwise.
        """
        result = await db[cls.collection].delete_one({"scene_id": scene_id})
        return result.deleted_count == 1

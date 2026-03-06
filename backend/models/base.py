"""
models/base.py
──────────────
Shared base classes and helpers for all MongoDB-backed models.

MongoDB stores the primary key as `_id` (ObjectId).  Pydantic models use
`id` (str) as the public-facing field, serialised from ObjectId via the
`PyObjectId` type.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any

from bson import ObjectId
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field


# ---------------------------------------------------------------------------
# ObjectId  ↔  str coercion
# ---------------------------------------------------------------------------

def _validate_object_id(v: Any) -> str:
    """Accept an ObjectId, a 24-hex string, or a plain str."""
    if isinstance(v, ObjectId):
        return str(v)
    if isinstance(v, str) and ObjectId.is_valid(v):
        return v
    raise ValueError(f"Invalid ObjectId: {v!r}")


PyObjectId = Annotated[str, BeforeValidator(_validate_object_id)]


# ---------------------------------------------------------------------------
# Base document model
# ---------------------------------------------------------------------------

class MongoBaseModel(BaseModel):
    """
    Every MongoDB document inherits from this class.

    • `id` maps to the `_id` field in MongoDB.
    • `created_at` / `updated_at` are set automatically.
    • Arbitrary `model_config` lets Pydantic handle ObjectId etc.
    """

    model_config = ConfigDict(
        populate_by_name=True,        # accept both `id` and `_id`
        arbitrary_types_allowed=True,
        protected_namespaces=(),       # allow field names like `model_used`
    )

    id: PyObjectId | None = Field(default=None, alias="_id")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

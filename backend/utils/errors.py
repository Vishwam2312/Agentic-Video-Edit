"""
utils/errors.py
───────────────
Shared HTTP exception helpers to keep router code terse.
"""

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status


def validate_object_id(value: str, field: str = "id") -> str:
    """
    Validate that *value* is a valid MongoDB ObjectId hex string.
    Raises HTTP 400 on failure, returns the value on success.
    """
    try:
        ObjectId(value)
        return value
    except (InvalidId, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{field}' is not a valid ObjectId: {value!r}.",
        )


def raise_not_found(resource: str, resource_id: str) -> None:
    """Raise HTTP 404 with a descriptive message."""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{resource} with id '{resource_id}' was not found.",
    )

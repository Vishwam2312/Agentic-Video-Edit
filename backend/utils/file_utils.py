"""
utils/file_utils.py
────────────────────
File I/O helpers for handling uploaded research-paper PDFs.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from backend.config import settings

# ---------------------------------------------------------------------------
# Directory constants
# ---------------------------------------------------------------------------

_ROOT = Path(settings.storage_root)

UPLOAD_DIR     = _ROOT / "uploads"
SCRIPTS_DIR    = _ROOT / "scripts"
SCENES_DIR     = _ROOT / "scenes"
ANIMATIONS_DIR = _ROOT / "animations"
AUDIO_DIR      = _ROOT / "audio"
VIDEOS_DIR     = _ROOT / "videos"
FINAL_DIR      = _ROOT / "final"

_ALLOWED_CONTENT_TYPES = {"application/pdf"}
_MAX_FILE_SIZE_BYTES   = 50 * 1024 * 1024  # 50 MB


def _ensure_dirs() -> None:
    """Create all storage subdirectories if they do not already exist."""
    for d in (UPLOAD_DIR, SCRIPTS_DIR, SCENES_DIR, ANIMATIONS_DIR, AUDIO_DIR, VIDEOS_DIR, FINAL_DIR):
        d.mkdir(parents=True, exist_ok=True)


_ensure_dirs()


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

async def save_upload_file(file: UploadFile, subdir: Path | None = None) -> str:
    """
    Read the uploaded file, validate it is a PDF within the size limit,
    write it to *subdir* (defaults to UPLOAD_DIR), and return the
    relative storage path as a string.

    Raises HTTPException 400 for wrong type or 413 for oversized files.
    """
    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only PDF files are accepted. Got: {file.content_type!r}.",
        )

    content: bytes = await file.read()

    if len(content) > _MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the 50 MB limit ({len(content)} bytes).",
        )

    target_dir = subdir or UPLOAD_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    # Build a collision-safe filename: <uuid>_<original>
    safe_name = f"{uuid.uuid4().hex}_{Path(file.filename or 'upload.pdf').name}"
    dest = target_dir / safe_name
    dest.write_bytes(content)

    # Return relative path (portable between OS)
    return str(dest.relative_to(Path(".")))

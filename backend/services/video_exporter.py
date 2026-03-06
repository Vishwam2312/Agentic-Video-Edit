"""
services/video_exporter.py
───────────────────────────
Assembles video from the subscene hierarchy and produces a final export.

Two-stage pipeline
------------------
1. assemble_scene(scene_id, db)
   Collects every subscene's video_ids, locates the corresponding MP4 chunks
   in storage/videos/, and concatenates them (FFmpeg concat demuxer) into a
   single per-scene MP4 stored in storage/videos/.

2. export_final_video(project_id, db)
   Fetches all scenes for the project, calls assemble_scene() for each one,
   then concatenates the assembled scene clips into a final MP4 stored in
   storage/final/.

Stream copy (-c copy) is used throughout for zero re-encoding loss.
FFmpeg must be installed and on PATH (or FFMPEG_PATH set in .env).
"""

from __future__ import annotations

import asyncio
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Optional
from typing import Optional

from loguru import logger
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.config import settings
from backend.services.database import Collections

_FINAL_DIR = Path(settings.storage_root) / "final"
_VIDEOS_DIR = Path(settings.storage_root) / "videos"
_FINAL_DIR.mkdir(parents=True, exist_ok=True)
_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)


# ── Public API ────────────────────────────────────────────────────────────────

async def assemble_scene(
    scene_id: str,
    *,
    db: AsyncIOMotorDatabase,
    output_stem: Optional[str] = None,
    timeout: int = 600,
) -> Path:
    """
    Concatenate all subscene video chunks for one scene into a single MP4.

    Workflow
    --------
    1. Fetch the scene document from MongoDB by ``scene_id`` (``_id``).
    2. Iterate over ``subscenes`` in order; collect each ``video_ids`` list.
    3. Resolve each ``video_id`` to ``storage/videos/<video_id>.mp4``.
    4. Concatenate via FFmpeg concat demuxer (stream copy).
    5. Save result to ``storage/videos/scene_<scene_id>.mp4``.

    Parameters
    ----------
    scene_id:
        The ``_id`` of the scene document.
    db:
        Motor database instance.
    output_stem:
        Output filename stem. Defaults to ``scene_<scene_id>``.
    timeout:
        Maximum seconds for the FFmpeg subprocess.

    Returns
    -------
    Path
        Absolute path to the assembled scene MP4 inside ``storage/videos/``.

    Raises
    ------
    ValueError
        If the scene is not found or has no renderable video chunks.
    FileNotFoundError
        If a referenced video chunk file does not exist on disk.
    RuntimeError
        If FFmpeg fails.
    """
    scene_doc = await db[Collections.SCENES].find_one({"_id": scene_id})
    if not scene_doc:
        raise ValueError(f"Scene '{scene_id}' not found in the database.")

    clips: list[Path] = []
    for subscene in scene_doc.get("subscenes", []):
        for video_id in subscene.get("video_ids", []):
            chunk_path = _VIDEOS_DIR / f"{video_id}.mp4"
            if not chunk_path.exists():
                raise FileNotFoundError(
                    f"Video chunk '{video_id}.mp4' not found at {chunk_path}. "
                    f"(subscene_id={subscene.get('subscene_id', '?')})"
                )
            clips.append(chunk_path)

    if not clips:
        raise ValueError(
            f"Scene '{scene_id}' has no renderable video chunks. "
            "Generate and render animations for its subscenes first."
        )

    stem = output_stem or f"scene_{scene_id}"
    output_path = _VIDEOS_DIR / f"{stem}.mp4"

    logger.info(
        "Assembling scene '{}': {} chunk(s) -> {}",
        scene_id,
        len(clips),
        output_path.name,
    )
    await _ffmpeg_concat(clips, output_path, timeout)
    return output_path


async def export_final_video(
    project_id: str,
    *,
    db: AsyncIOMotorDatabase,
    output_stem: Optional[str] = None,
    timeout: int = 600,
) -> Path:
    """
    Assemble every scene in the project and concatenate them into a final MP4.

    Workflow
    --------
    1. Fetch all scenes for the project (sorted by ``created_at``).
    2. For each scene call :func:`assemble_scene` to produce a per-scene clip.
    3. Concatenate all per-scene clips into a final MP4 in ``storage/final/``.

    Parameters
    ----------
    project_id:
        Project identifier used to query the scenes collection.
    db:
        Motor database instance.
    output_stem:
        Output filename stem. Defaults to ``final_<uuid>``.
    timeout:
        Maximum seconds for each FFmpeg call.

    Returns
    -------
    Path
        Absolute path to the final MP4 inside ``storage/final/``.

    Raises
    ------
    ValueError
        If no scenes are found for the project.
    FileNotFoundError
        If a video chunk is missing from disk.
    RuntimeError
        If FFmpeg fails at any stage.
    """
    cursor = db[Collections.SCENES].find(
        {"project_id": project_id},
        sort=[("created_at", 1)],
    )
    scenes = await cursor.to_list(length=None)

    if not scenes:
        raise ValueError(
            f"No scenes found for project '{project_id}'. "
            "Create scenes and render their subscenes first."
        )

    scene_clips: list[Path] = []
    for scene in scenes:
        scene_id = str(scene["_id"])
        clip = await assemble_scene(scene_id, db=db, timeout=timeout)
        scene_clips.append(clip)
        logger.info("Scene '{}' assembled -> {}", scene_id, clip.name)

    stem = output_stem or f"final_{uuid.uuid4().hex[:12]}"
    output_path = _FINAL_DIR / f"{stem}.mp4"

    logger.info(
        "Exporting final video: {} scene clip(s) -> {}",
        len(scene_clips),
        output_path.name,
    )
    await _ffmpeg_concat(scene_clips, output_path, timeout)
    return output_path


# ── Helpers ─────────────────────────────────────────────────────────────────

async def _ffmpeg_concat(clips: list[Path], output_path: Path, timeout: int) -> None:
    """
    Concatenate ``clips`` into ``output_path`` using the FFmpeg concat demuxer
    with stream copy (no re-encoding).

    Raises
    ------
    RuntimeError
        If FFmpeg exits non-zero or the output file is absent.
    asyncio.TimeoutError
        If the subprocess exceeds ``timeout`` seconds.
    """
    ffmpeg_exe = _resolve_ffmpeg()

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".txt",
        delete=False,
        encoding="utf-8",
        prefix="explainai_concat_",
    ) as concat_file:
        concat_path = Path(concat_file.name)
        for clip in clips:
            concat_file.write(f"file '{clip.resolve()}'\n")

    cmd = [
        ffmpeg_exe,
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_path),
        "-c", "copy",
        str(output_path),
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        _, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        concat_path.unlink(missing_ok=True)
        raise asyncio.TimeoutError(
            f"FFmpeg concat timed out after {timeout}s → {output_path.name}"
        )
    finally:
        concat_path.unlink(missing_ok=True)

    stderr = stderr_bytes.decode(errors="replace")
    if proc.returncode != 0:
        logger.error("FFmpeg concat stderr:\n{}", stderr[-3000:])
        raise RuntimeError(
            f"FFmpeg exited with code {proc.returncode}.\n"
            f"stderr (last 2000 chars):\n{stderr[-2000:]}"
        )

    if not output_path.exists():
        raise RuntimeError(
            f"FFmpeg completed but output file not found: {output_path}"
        )

    size = output_path.stat().st_size
    logger.info("FFmpeg concat complete -> {} ({} bytes)", output_path.name, size)


def _resolve_ffmpeg() -> str:
    explicit = getattr(settings, "ffmpeg_path", "")
    if explicit:
        return explicit
    venv_bin = Path(sys.executable).parent
    for candidate in (venv_bin / "ffmpeg.exe", venv_bin / "ffmpeg"):
        if candidate.exists():
            return str(candidate)
    return "ffmpeg"

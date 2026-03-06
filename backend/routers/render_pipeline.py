"""
routers/render_pipeline.py
───────────────────────────
Single-endpoint rendering pipeline.

POST /render
    1. Fetch script from the ``scripts`` collection.
    2. Generate scenes (LLM) → list[SceneItem].
    3. For every subscene: generate Manim animation code (LLM).
    4. Render each animation with Manim → MP4 chunk.
    5. Concatenate all chunks with FFmpeg → final MP4.
    6. Return the relative URL of the final video.

No TTS or audio-video sync is involved.
"""

from __future__ import annotations

import asyncio
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from backend.agents.animation_agent import generate_animation_code
from backend.agents.scene_agent import generate_scenes
from backend.config import settings
from backend.services.animation_renderer import render_scene
from backend.services.database import db_dependency
from backend.services.repositories import ScriptRepository

router = APIRouter(tags=["Render"])

_FINAL_DIR = Path(settings.storage_root) / "final"
_FINAL_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class RenderRequest(BaseModel):
    script_id: str


class RenderResponse(BaseModel):
    video_url: str
    scene_count: int
    chunk_count: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _ffmpeg_concat(clips: list[Path], output: Path, timeout: int = 600) -> None:
    """Concatenate *clips* into *output* using the FFmpeg concat demuxer."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as fh:
        for clip in clips:
            fh.write(f"file '{clip.as_posix()}'\n")
        list_file = Path(fh.name)

    ffmpeg_exe = getattr(settings, "ffmpeg_path", None) or "ffmpeg"
    cmd = [
        ffmpeg_exe,
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        str(output),
    ]
    logger.info("FFmpeg concat: {} clips -> {}", len(clips), output.name)
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        if proc.returncode != 0:
            raise RuntimeError(
                f"FFmpeg exited {proc.returncode}: {stderr.decode()[-500:]}"
            )
    finally:
        list_file.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# POST /render
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=RenderResponse,
    status_code=status.HTTP_200_OK,
    summary="Run full render pipeline from script to final MP4",
    description=(
        "Fetches the script, generates scenes via LLM, generates a Manim "
        "animation for each subscene, renders to MP4 chunks, concatenates "
        "all chunks into one final video, and returns its URL."
    ),
)
async def render_pipeline(
    payload: RenderRequest,
    db: AsyncIOMotorDatabase = Depends(db_dependency),
) -> RenderResponse:

    # ── 1. Fetch script ───────────────────────────────────────────────────────
    script_doc = await ScriptRepository.get_script(db, payload.script_id)
    if not script_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Script '{payload.script_id}' not found.",
        )

    # Build the dict shape expected by generate_scenes()
    script_payload = {
        "title": script_doc.get("title", ""),
        "sections": [
            {"heading": script_doc.get("title", ""), "text": script_doc.get("content", "")}
        ],
    }

    # ── 2. Generate scenes ────────────────────────────────────────────────────
    logger.info("render_pipeline: generating scenes for script '{}'", payload.script_id)
    try:
        scene_items = await generate_scenes(script_payload)
    except Exception as exc:
        logger.error("Scene generation failed: {}", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Scene generation failed: {exc}",
        ) from exc

    # ── 3 & 4. Generate animation code + render each subscene ─────────────────
    all_chunks: list[Path] = []   # every rendered MP4 chunk in order
    scene_count = len(scene_items)

    for s_idx, scene in enumerate(scene_items):
        logger.info(
            "render_pipeline: scene {}/{} '{}' — {} subscene(s)",
            s_idx + 1, scene_count, scene.scene_title, len(scene.subscenes),
        )
        for sub_idx, subscene in enumerate(scene.subscenes):
            subscene_label = f"scene{s_idx + 1}_sub{sub_idx + 1}"
            try:
                manim_code = await generate_animation_code({
                    "text": subscene.text,
                    "visual_description": subscene.visual_description,
                    "index": sub_idx,
                })
            except Exception as exc:
                logger.error(
                    "Animation generation failed for {}: {}", subscene_label, exc
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Animation generation failed for {subscene_label}: {exc}",
                ) from exc

            try:
                result = await render_scene(manim_code, stem=subscene_label)
            except Exception as exc:
                logger.error("Manim render failed for {}: {}", subscene_label, exc)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Manim render failed for {subscene_label}: {exc}",
                ) from exc

            all_chunks.append(result.path)
            logger.info("  rendered {} -> {}", subscene_label, result.path.name)

    if not all_chunks:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Pipeline produced no video chunks.",
        )

    # ── 5. Concatenate all chunks into one final MP4 ───────────────────────────
    final_stem = f"render_{payload.script_id[:8]}_{uuid.uuid4().hex[:8]}"
    final_path = _FINAL_DIR / f"{final_stem}.mp4"

    if len(all_chunks) == 1:
        import shutil
        shutil.copy2(all_chunks[0], final_path)
    else:
        try:
            await _ffmpeg_concat(all_chunks, final_path)
        except Exception as exc:
            logger.error("FFmpeg concat failed: {}", exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Video concatenation failed: {exc}",
            ) from exc

    # ── 6. Return result ──────────────────────────────────────────────────────
    relative_url = f"/storage/final/{final_path.name}"
    logger.info(
        "render_pipeline complete: {} scenes, {} chunks -> {}",
        scene_count, len(all_chunks), final_path.name,
    )
    return RenderResponse(
        video_url=relative_url,
        scene_count=scene_count,
        chunk_count=len(all_chunks),
    )

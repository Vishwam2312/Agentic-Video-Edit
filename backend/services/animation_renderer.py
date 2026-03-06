"""
services/animation_renderer.py
────────────────────────────────
Async wrapper around the Manim Community Edition CLI.

Takes Manim Python source code, runs it in an isolated temp directory,
locates the output MP4, moves it to storage/videos/, and returns both
the file path and a stable video_id string.

The video_id is the output file stem (UUID-based), making it safe to store
directly in subscene.video_ids[].

Manim must be installed in the same Python environment:
    pip install manim
"""

from __future__ import annotations

import asyncio
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

from dataclasses import dataclass

from loguru import logger

from backend.config import settings

_VIDEOS_DIR = Path(settings.storage_root) / "videos"
_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

# Manim quality flag → (label, expected subfolder glob)
# Use "l" (low / 480p15) by default for fast renders during development.
# Override via MANIM_QUALITY env var if needed.
_DEFAULT_QUALITY = "l"  # -ql flag


@dataclass
class RenderResult:
    """
    Returned by :func:`render_scene` after a successful Manim render.

    Attributes
    ----------
    video_id:
        Stable identifier for the rendered video chunk.  Equal to the output
        file stem (UUID-based).  Store this in ``subscene.video_ids[]``.
    path:
        Absolute :class:`~pathlib.Path` to the MP4 file on disk.
    """

    video_id: str
    path: Path


# ── Public API ────────────────────────────────────────────────────────────────

async def render_scene(
    manim_code: str,
    *,
    stem: str | None = None,
    quality: str = _DEFAULT_QUALITY,
    timeout: int = 300,
) -> RenderResult:
    """
    Render a Manim animation and return a :class:`RenderResult` containing
    the ``video_id`` and the path to the output MP4.

    The ``video_id`` is the file stem of the saved MP4 and is suitable for
    storing directly in ``subscene.video_ids[]``.

    Parameters
    ----------
    manim_code:
        Complete Manim Python source containing a ``SceneAnimation`` class.
    stem:
        Base name (no extension) for the output file.
        Defaults to a UUID.
    quality:
        Manim quality flag character: ``l`` (480p), ``m`` (720p), ``h`` (1080p).
    timeout:
        Maximum seconds allowed for the Manim subprocess.

    Returns
    -------
    RenderResult
        ``.video_id`` — stable chunk identifier (file stem).
        ``.path``     — absolute path to the MP4 on disk.

    Raises
    ------
    RuntimeError
        If Manim exits with a non-zero code or no MP4 is found.
    asyncio.TimeoutError
        If the render exceeds ``timeout`` seconds.
    FileNotFoundError
        If the ``manim`` executable is not on PATH.
    """
    output_stem = stem or f"scene_{uuid.uuid4().hex[:12]}"

    with tempfile.TemporaryDirectory(prefix="explainai_manim_") as tmpdir:
        tmp_path = Path(tmpdir)

        # Write the Manim script
        script_file = tmp_path / f"{output_stem}.py"
        script_file.write_text(manim_code, encoding="utf-8")

        # Resolve the manim executable: prefer the venv copy so the same
        # Python environment is used (important for any manim plugins).
        manim_exe = _resolve_manim_exe()

        cmd = [
            manim_exe,
            f"-q{quality}",
            "--output_file", output_stem,
            "--media_dir", str(tmp_path / "media"),
            "--disable_caching",
            str(script_file),
            "SceneAnimation",
        ]

        logger.info("Running Manim: {}", " ".join(cmd))

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            raise asyncio.TimeoutError(
                f"Manim render timed out after {timeout}s for '{output_stem}'"
            )

        stdout = stdout_bytes.decode(errors="replace")
        stderr = stderr_bytes.decode(errors="replace")

        if proc.returncode != 0:
            logger.error("Manim stderr:\n{}", stderr[-3000:])
            raise RuntimeError(
                f"Manim exited with code {proc.returncode}.\n"
                f"stderr (last 2000 chars):\n{stderr[-2000:]}"
            )

        logger.debug("Manim stdout:\n{}", stdout[-1000:])

        # Locate the produced MP4 (Manim nests it in media/videos/<name>/<quality>/)
        mp4_files = list((tmp_path / "media").rglob("*.mp4"))
        if not mp4_files:
            raise RuntimeError(
                f"Manim completed successfully but no MP4 was found under {tmp_path / 'media'}.\n"
                f"stdout:\n{stdout[-1000:]}"
            )

        # Prefer the file matching our stem; fall back to the first found
        target = next(
            (f for f in mp4_files if f.stem == output_stem),
            mp4_files[0],
        )

        dest = _VIDEOS_DIR / f"{output_stem}.mp4"
        shutil.move(str(target), str(dest))
        logger.info("Render complete → {} (video_id={})", dest, output_stem)
        return RenderResult(video_id=output_stem, path=dest)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _resolve_manim_exe() -> str:
    """
    Return the path to the manim executable.
    Prefers the venv's own binary so plugins installed there are available.
    Falls back to whatever is on PATH.
    """
    venv_manim = Path(sys.executable).parent / "manim"
    if venv_manim.exists():
        return str(venv_manim)
    venv_manim_win = Path(sys.executable).parent / "manim.exe"
    if venv_manim_win.exists():
        return str(venv_manim_win)
    # Fallback — let the OS find it
    return "manim"

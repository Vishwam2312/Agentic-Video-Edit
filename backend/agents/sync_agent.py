"""
agents/sync_agent.py
─────────────────────
Merges a rendered scene video (MP4) with its synthesized audio (WAV) using
the FFmpeg CLI.

FFmpeg must be installed and accessible on PATH (or set FFMPEG_PATH in .env).

Strategy
--------
- The audio track completely replaces the silent Manim video's audio track.
- If the audio is shorter than the video, the video is trimmed to match.
- If the audio is longer, it is trimmed to the video length.
  This keeps the output clean — no dead air or missing frames.

Output
------
storage/videos/<stem>_synced.mp4  (H.264 + AAC, web-ready)
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from loguru import logger

from backend.config import settings

_VIDEOS_DIR = Path(settings.storage_root) / "videos"
_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)


# ── Public API ────────────────────────────────────────────────────────────────

async def sync_audio_video(
    video_path: str | Path,
    audio_path: str | Path,
    *,
    output_stem: str | None = None,
    timeout: int = 120,
) -> Path:
    """
    Merge ``audio_path`` into ``video_path`` using FFmpeg and save the result.

    Parameters
    ----------
    video_path:
        Path to the silent rendered scene MP4 (e.g. from Manim).
    audio_path:
        Path to the synthesized audio WAV (e.g. from Coqui TTS).
    output_stem:
        Base filename (no extension) for the output file.
        Defaults to ``<video_stem>_synced``.
    timeout:
        Maximum seconds allowed for the FFmpeg process.

    Returns
    -------
    Path
        Absolute path to the synced MP4 inside ``storage/videos/``.

    Raises
    ------
    FileNotFoundError
        If either input file does not exist.
    RuntimeError
        If FFmpeg exits with a non-zero code.
    asyncio.TimeoutError
        If the merge exceeds ``timeout`` seconds.
    """
    video_path = Path(video_path)
    audio_path = Path(audio_path)

    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    stem = output_stem or f"{video_path.stem}_synced"
    output_path = _VIDEOS_DIR / f"{stem}.mp4"

    ffmpeg_exe = _resolve_ffmpeg()

    # FFmpeg command:
    #   -i video   — input 0: video stream
    #   -i audio   — input 1: audio stream
    #   -map 0:v:0 — take video from input 0
    #   -map 1:a:0 — take audio from input 1
    #   -c:v copy  — copy video stream without re-encoding (fast)
    #   -c:a aac   — encode audio to AAC for MP4 compatibility
    #   -shortest  — end at the shorter of the two streams
    #   -y         — overwrite output without prompting
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(output_path),
    ]

    logger.info("Running FFmpeg sync: {} + {} → {}", video_path.name, audio_path.name, output_path.name)

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
        raise asyncio.TimeoutError(
            f"FFmpeg sync timed out after {timeout}s for '{stem}'"
        )

    stderr = stderr_bytes.decode(errors="replace")

    if proc.returncode != 0:
        logger.error("FFmpeg stderr:\n{}", stderr[-3000:])
        raise RuntimeError(
            f"FFmpeg exited with code {proc.returncode}.\n"
            f"stderr (last 2000 chars):\n{stderr[-2000:]}"
        )

    if not output_path.exists():
        raise RuntimeError(
            f"FFmpeg completed but output file not found: {output_path}"
        )

    logger.info("Sync complete → {} ({} bytes)", output_path.name, output_path.stat().st_size)
    return output_path


# ── Helpers ───────────────────────────────────────────────────────────────────

def _resolve_ffmpeg() -> str:
    """
    Return the path to the ffmpeg executable.
    Priority:
      1. FFMPEG_PATH setting (explicit override)
      2. ffmpeg.exe / ffmpeg next to the Python executable (venv bin)
      3. Plain 'ffmpeg' — rely on system PATH
    """
    explicit = getattr(settings, "ffmpeg_path", "")
    if explicit:
        return explicit

    venv_bin = Path(sys.executable).parent
    for candidate in (venv_bin / "ffmpeg.exe", venv_bin / "ffmpeg"):
        if candidate.exists():
            return str(candidate)

    return "ffmpeg"

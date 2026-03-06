"""
agents/highlight_agent.py
──────────────────────────
Detects highlight segments in a video by analysing sampled frames and the
scene transcript using GPT-4o vision (or any OpenAI-compatible vision model).

Pipeline
--------
1. Extract one keyframe per second from the video via FFmpeg (JPEG thumbnails).
2. Encode frames as base64 and bundle them with the transcript.
3. Send a single multi-modal prompt to the LLM.
4. Parse the JSON response into typed HighlightSegment objects.

The LLM receives both visual context (frames) and textual context (transcript)
so it can find moments where interesting things are shown AND said.
"""

from __future__ import annotations

import asyncio
import base64
import json
import re
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from loguru import logger
from openai import AsyncOpenAI

from backend.config import settings

# Maximum frames sent to the LLM — stay within token/image limits.
# GPT-4o supports up to ~20 images comfortably per request.
_MAX_FRAMES = 16

# FFmpeg interval: extract one frame every N seconds
_FRAME_INTERVAL_S = 3


# ── Output schema ─────────────────────────────────────────────────────────────

@dataclass
class HighlightSegment:
    start_s: float          # start time in seconds
    end_s: float            # end time in seconds
    label: str              # short title for the highlight
    score: float            # confidence / importance 0.0–1.0
    reason: str             # why this moment is a highlight
    focus_words: list[str] = field(default_factory=list)  # key terms in segment

    @property
    def duration_s(self) -> float:
        return max(0.0, self.end_s - self.start_s)

    def to_dict(self) -> dict:
        return {
            "start_s": self.start_s,
            "end_s": self.end_s,
            "label": self.label,
            "score": self.score,
            "reason": self.reason,
            "focus_words": self.focus_words,
            "duration_s": self.duration_s,
        }


# ── System prompt ─────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are an expert video editor and instructional designer specialising in \
educational explainer videos.

You will receive:
1. A series of video frames (JPEG thumbnails) sampled at regular intervals.
2. The full narration transcript of the video, with approximate timestamps.

Your task: identify the most compelling highlight segments — moments worth \
re-watching, sharing, or using as preview clips.

Output MUST be valid JSON — a top-level array, no markdown fences:

[
  {
    "start_s": <float, seconds>,
    "end_s": <float, seconds>,
    "label": "<short title ≤ 8 words>",
    "score": <float 0.0-1.0, higher = more important>,
    "reason": "<1-2 sentences explaining why this is a highlight>",
    "focus_words": ["<key term>", ...]
  }
]

Guidelines:
- Return 3–8 highlights ordered by start time.
- A highlight should be at least 3 seconds long and at most 30 seconds.
- Prefer moments where an important concept is introduced or clearly visualised.
- score 1.0 = the single most important moment; score 0.5 = moderately interesting.
- focus_words: 2–4 key technical terms visible or spoken in the segment.
"""


# ── Public API ────────────────────────────────────────────────────────────────

async def generate_highlights(
    video_path: str | Path,
    transcript: str,
    *,
    model: str | None = None,
    frame_interval_s: int = _FRAME_INTERVAL_S,
    max_frames: int = _MAX_FRAMES,
) -> list[HighlightSegment]:
    """
    Detect highlight segments in a video using vision + transcript analysis.

    Parameters
    ----------
    video_path:
        Path to the MP4 video file (final export or individual synced scene).
    transcript:
        Full narration text. If structured (e.g. from scene narration_text
        joined together), include it as plain prose.
    model:
        Vision-capable model to use. Defaults to ``settings.openai_model``.
        Must support image inputs (e.g. ``gpt-4o``, ``gpt-4o-mini``).
    frame_interval_s:
        Extract one frame every this many seconds (lower = more frames).
    max_frames:
        Cap on frames sent to the LLM to stay within token limits.

    Returns
    -------
    list[HighlightSegment]
        Ordered list of highlight segments.

    Raises
    ------
    FileNotFoundError
        If ``video_path`` does not exist.
    ValueError
        If the LLM returns malformed JSON.
    openai.OpenAIError
        Propagated directly.
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    resolved_model = model or settings.openai_model

    # 1. Extract keyframes
    frames = await _extract_frames(video_path, frame_interval_s, max_frames)
    logger.info(
        "Highlight detection — model={} frames={} transcript_len={}",
        resolved_model,
        len(frames),
        len(transcript),
    )

    # 2. Build the multi-modal message
    video_duration_s = len(frames) * frame_interval_s
    transcript_block = _build_transcript_block(
        transcript, video_duration_s, frames, frame_interval_s
    )

    content: list[dict] = [
        {"type": "text", "text": transcript_block},
    ]
    for ts, b64 in frames:
        content.append({
            "type": "text",
            "text": f"Frame at {ts:.1f}s:",
        })
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{b64}",
                "detail": "low",   # low detail = fewer tokens, sufficient for highlights
            },
        })

    client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url or None,
    )

    response = await client.chat.completions.create(
        model=resolved_model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
        temperature=0.3,
        response_format={"type": "json_object"},
    )

    raw = (response.choices[0].message.content or "").strip()
    logger.debug("Highlight LLM response — {} chars", len(raw))
    return _parse_response(raw)


# ── Frame extraction ──────────────────────────────────────────────────────────

async def _extract_frames(
    video_path: Path,
    interval_s: int,
    max_frames: int,
) -> list[tuple[float, str]]:
    """
    Extract JPEG frames every ``interval_s`` seconds using FFmpeg.

    Returns a list of (timestamp_seconds, base64_jpeg_string) tuples.
    """
    ffmpeg_exe = _resolve_ffmpeg()

    with tempfile.TemporaryDirectory(prefix="explainai_frames_") as tmpdir:
        out_pattern = str(Path(tmpdir) / "frame_%04d.jpg")

        cmd = [
            ffmpeg_exe,
            "-i", str(video_path),
            "-vf", f"fps=1/{interval_s}",
            "-q:v", "5",          # JPEG quality 1 (best) – 31 (worst); 5 is good
            "-frames:v", str(max_frames),
            out_pattern,
            "-y",
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=60)

        if proc.returncode != 0:
            stderr = stderr_bytes.decode(errors="replace")
            raise RuntimeError(
                f"FFmpeg frame extraction failed (code {proc.returncode}):\n{stderr[-1000:]}"
            )

        frame_files = sorted(Path(tmpdir).glob("frame_*.jpg"))
        if not frame_files:
            logger.warning("No frames extracted from {}; returning empty list", video_path.name)
            return []

        result: list[tuple[float, str]] = []
        for i, fp in enumerate(frame_files[:max_frames]):
            ts = float(i * interval_s)
            b64 = base64.b64encode(fp.read_bytes()).decode("ascii")
            result.append((ts, b64))

        return result


def _build_transcript_block(
    transcript: str,
    video_duration_s: float,
    frames: list[tuple[float, str]],
    interval_s: int,
) -> str:
    return (
        f"Video duration: approximately {video_duration_s:.0f} seconds\n"
        f"Frames sampled every {interval_s}s ({len(frames)} total)\n\n"
        f"Full narration transcript:\n{transcript[:6000]}\n\n"
        "Identify the highlight segments from this video using both the "
        "transcript and the visual frames shown below."
    )


# ── Response parsing ──────────────────────────────────────────────────────────

def _parse_response(raw: str) -> list[HighlightSegment]:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Highlight agent returned non-JSON: {exc}\n\nRaw:\n{raw[:500]}"
        ) from exc

    # Unwrap {"highlights": [...]} or similar wrapper
    if isinstance(data, dict):
        data = next((v for v in data.values() if isinstance(v, list)), [])

    if not isinstance(data, list):
        raise ValueError(f"Expected JSON array, got {type(data)}")

    highlights: list[HighlightSegment] = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            continue
        try:
            start = float(item.get("start_s", 0))
            end = float(item.get("end_s", start + 5))
            label = str(item.get("label", f"Highlight {i + 1}")).strip()
            score = max(0.0, min(1.0, float(item.get("score", 0.5))))
            reason = str(item.get("reason", "")).strip()
            focus_words = [
                str(w).strip()
                for w in item.get("focus_words", [])
                if str(w).strip()
            ]
            if end <= start:
                logger.warning("highlights[{}] has end <= start — skipped", i)
                continue
            highlights.append(
                HighlightSegment(
                    start_s=round(start, 2),
                    end_s=round(end, 2),
                    label=label,
                    score=round(score, 3),
                    reason=reason,
                    focus_words=focus_words,
                )
            )
        except (TypeError, ValueError) as exc:
            logger.warning("highlights[{}] parse error — skipped: {}", i, exc)

    return sorted(highlights, key=lambda h: h.start_s)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _resolve_ffmpeg() -> str:
    explicit = getattr(settings, "ffmpeg_path", "")
    if explicit:
        return explicit
    venv_bin = Path(sys.executable).parent
    for candidate in (venv_bin / "ffmpeg.exe", venv_bin / "ffmpeg"):
        if candidate.exists():
            return str(candidate)
    return "ffmpeg"

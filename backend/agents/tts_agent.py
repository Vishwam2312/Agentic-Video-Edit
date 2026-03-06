"""
agents/tts_agent.py
────────────────────
Converts scene narration text to speech using Coqui TTS (TTS library).

Coqui TTS runs fully locally — no API key required.
Install: pip install TTS

Default model: tts_models/en/ljspeech/tacotron2-DDC
Override via TTS_MODEL env var in .env for multilingual or neural models.

The synthesized audio is saved as a WAV file to storage/audio/.
"""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

from loguru import logger

from backend.config import settings

_AUDIO_DIR = Path(settings.storage_root) / "audio"
_AUDIO_DIR.mkdir(parents=True, exist_ok=True)


# ── Public API ────────────────────────────────────────────────────────────────

async def generate_audio(
    scene_text: str,
    *,
    stem: str | None = None,
    model_name: str | None = None,
) -> Path:
    """
    Synthesize speech from ``scene_text`` and save it as a WAV file.

    Parameters
    ----------
    scene_text:
        The narration text to synthesize (scene's ``narration_text`` field).
    stem:
        Base filename (no extension) for the output WAV.
        Defaults to a UUID.
    model_name:
        Coqui TTS model identifier to use.
        Defaults to ``settings.tts_model``.

    Returns
    -------
    Path
        Absolute path to the saved ``.wav`` file inside ``storage/audio/``.

    Raises
    ------
    ImportError
        If the ``TTS`` package is not installed.
    RuntimeError
        If synthesis produces an empty or missing file.
    """
    try:
        from TTS.api import TTS  # noqa: PLC0415 — deferred import
    except ImportError as exc:
        raise ImportError(
            "Coqui TTS is not installed. Run: pip install TTS"
        ) from exc

    resolved_model = model_name or settings.tts_model
    output_stem = stem or f"audio_{uuid.uuid4().hex[:12]}"
    output_path = _AUDIO_DIR / f"{output_stem}.wav"

    logger.info(
        "Synthesizing TTS — model={} text_length={} output={}",
        resolved_model,
        len(scene_text),
        output_path.name,
    )

    # TTS synthesis is CPU-bound; run in a thread to avoid blocking the event loop
    await asyncio.to_thread(
        _synthesize_sync,
        resolved_model,
        scene_text,
        output_path,
    )

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError(
            f"TTS synthesis completed but output file is missing or empty: {output_path}"
        )

    logger.info("Audio saved → {} ({} bytes)", output_path.name, output_path.stat().st_size)
    return output_path


# ── Internal helpers ──────────────────────────────────────────────────────────

def _synthesize_sync(model_name: str, text: str, output_path: Path) -> None:
    """
    Blocking TTS call — intended to be run via ``asyncio.to_thread``.
    Downloads the model on first use (cached by Coqui in ~/.local/share/tts/).
    """
    from TTS.api import TTS  # noqa: PLC0415

    tts = TTS(model_name=model_name, progress_bar=False)
    tts.tts_to_file(text=text, file_path=str(output_path))

"""
agents/script_agent.py
───────────────────────
Converts research-paper text into a structured educational video script using
an OpenAI-compatible LLM API.

Works with any OpenAI-compatible provider — swap OPENAI_BASE_URL to point at
Ollama, Together.ai, Azure OpenAI, LiteLLM, Groq, etc.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from loguru import logger
from openai import AsyncOpenAI

from backend.config import settings


# ── Output schema ─────────────────────────────────────────────────────────────

@dataclass
class ScriptSection:
    heading: str
    text: str


@dataclass
class ScriptResult:
    title: str
    sections: list[ScriptSection]

    @property
    def full_text(self) -> str:
        """Flat narration text — all sections joined, suitable for word-count."""
        return "\n\n".join(f"{s.heading}\n{s.text}" for s in self.sections)

    @property
    def word_count(self) -> int:
        return len(self.full_text.split())

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "sections": [{"heading": s.heading, "text": s.text} for s in self.sections],
        }


# ── System prompt ─────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are an expert science communicator who converts academic research papers \
into clear, engaging educational video scripts for a general but curious audience.

Your output MUST be valid JSON in exactly this structure \
(no markdown fences, no extra keys):

{
  "title": "<short punchy video title>",
  "sections": [
    {
      "heading": "<section heading>",
      "text": "<2-4 sentences of plain prose for that section>"
    }
  ]
}

Guidelines:
- Use simple language (aim for a 9th-grade reading level).
- Keep each section text to 2-4 natural spoken sentences.
- Produce 5-8 sections that together tell a coherent story.
- Do NOT use bullet points or markdown inside the text fields.
- The title must be engaging and ≤ 12 words.
"""

# Maximum characters sent to the LLM to stay within common context windows.
# 12 000 chars ≈ ~3 000 tokens — safe for 8k-context models.
_MAX_CHARS = 12_000


# ── Public API ────────────────────────────────────────────────────────────────

async def generate_script(
    document_text: str,
    *,
    model: str | None = None,
) -> ScriptResult:
    """
    Convert research-paper text into a structured educational script.

    Parameters
    ----------
    document_text:
        Full extracted text from the PDF (from pdf_parser).
    model:
        Override the model configured in settings (useful for A/B testing or
        temporary hot-swapping without restarting the server).

    Returns
    -------
    ScriptResult
        Typed object with ``title``, ``sections``, ``full_text``, ``word_count``.

    Raises
    ------
    ValueError
        If the LLM returns malformed JSON or a response missing required keys.
    openai.OpenAIError
        Propagated directly for upstream error handling / retries.
    """
    resolved_model = model or settings.openai_model

    client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        # None falls back to the default OpenAI endpoint
        base_url=settings.openai_base_url or None,
    )

    # Truncate very long documents to avoid exceeding the context window.
    truncated = document_text[:_MAX_CHARS]
    if len(document_text) > _MAX_CHARS:
        logger.warning(
            "Document text truncated from {} to {} chars for LLM context",
            len(document_text),
            _MAX_CHARS,
        )

    logger.info("Requesting script generation — model={}", resolved_model)

    response = await client.chat.completions.create(
        model=resolved_model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": f"Research paper text:\n\n{truncated}"},
        ],
        temperature=0.4,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content or ""
    logger.debug("LLM response received — length={} chars", len(raw))

    return _parse_response(raw)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _parse_response(raw: str) -> ScriptResult:
    """Validate and parse the LLM JSON string into a ``ScriptResult``."""
    # Strip accidental markdown code fences that some models emit
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)

    try:
        data: dict = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"LLM returned non-JSON content: {exc}\n\nRaw response:\n{raw[:500]}"
        ) from exc

    if "title" not in data:
        raise ValueError(
            f"LLM response missing required 'title' key. Keys found: {list(data.keys())}"
        )
    if "sections" not in data or not isinstance(data["sections"], list):
        raise ValueError(
            f"LLM response missing or invalid 'sections'. Keys found: {list(data.keys())}"
        )

    sections: list[ScriptSection] = []
    for i, item in enumerate(data["sections"]):
        if not isinstance(item, dict):
            raise ValueError(f"sections[{i}] is not a JSON object")
        heading = str(item.get("heading", "")).strip()
        text = str(item.get("text", "")).strip()
        if not heading or not text:
            logger.warning("sections[{}] has empty heading or text — skipped", i)
            continue
        sections.append(ScriptSection(heading=heading, text=text))

    if not sections:
        raise ValueError("LLM response contains no valid sections after parsing")

    return ScriptResult(title=str(data["title"]).strip(), sections=sections)

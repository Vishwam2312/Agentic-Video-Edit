"""
agents/scene_agent.py
──────────────────────
Breaks a structured script into scenes, each containing multiple subscenes,
using an OpenAI-compatible LLM.

Hierarchy produced
------------------
Scene
├── scene_title
└── subscenes[]
       ├── text                (narration for this subscene)
       └── visual_description  (animation prompt for this subscene)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from loguru import logger
from openai import AsyncOpenAI

from backend.config import settings


# ── Output schema ─────────────────────────────────────────────────────────────

@dataclass
class SubSceneItem:
    text: str               # narration spoken in this subscene
    visual_description: str # animation / illustration prompt


@dataclass
class SceneItem:
    scene_title: str
    subscenes: list[SubSceneItem] = field(default_factory=list)


# ── System prompt ─────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are a visual content director and instructional designer who plans \
educational explainer videos.

You will receive a structured educational script (title + sections). \
Your job is to break it into scenes, where each scene covers one topic \
and contains 2-4 subscenes. Each subscene is a short visual beat \
that can be independently animated.

Output MUST be valid JSON — a top-level array, no markdown fences:

[
  {
    "scene_title": "<descriptive title for this scene>",
    "subscenes": [
      {
        "text": "<narration text, 1-2 natural spoken sentences>",
        "visual_description": "<what should be shown/animated on screen, \
1 sentence, rich visual detail for an animator>"
      }
    ]
  }
]

Guidelines:
- Produce between 3 and 8 scenes total.
- Each scene must have 2–4 subscenes.
- text must be natural spoken prose — no bullet points or markdown.
- visual_description should describe the on-screen visuals concisely \
(e.g. "A 3D diagram of a neural network with glowing activation nodes").
- Keep each subscene focused on a single visual idea.
"""


# ── Public API ────────────────────────────────────────────────────────────────

async def generate_scenes(
    script: dict,
    *,
    model: str | None = None,
) -> list[SceneItem]:
    """
    Break a structured script into scenes with subscenes.

    Parameters
    ----------
    script:
        Dict with keys ``title`` (str) and ``sections``
        (list of ``{"heading": str, "text": str}``).
    model:
        Optional model override; falls back to ``settings.openai_model``.

    Returns
    -------
    list[SceneItem]
        Ordered list of scenes, each containing a list of
        :class:`SubSceneItem` objects.

    Raises
    ------
    ValueError
        If the LLM output is malformed or contains no scenes.
    openai.OpenAIError
        Propagated directly for upstream handling.
    """
    resolved_model = model or settings.openai_model

    client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url or None,
    )

    user_content = _format_script(script)
    logger.info(
        "Requesting scene planning — model={} sections={}",
        resolved_model,
        len(script.get("sections", [])),
    )

    response = await client.chat.completions.create(
        model=resolved_model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.4,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content or ""
    logger.debug("Scene LLM response — {} chars", len(raw))
    return _parse_response(raw)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _format_script(script: dict) -> str:
    """Serialize the script dict into a compact text block for the LLM."""
    title = script.get("title", "Untitled")
    sections = script.get("sections", [])
    lines = [f"Title: {title}", ""]
    for i, sec in enumerate(sections, 1):
        heading = sec.get("heading", f"Section {i}")
        text = sec.get("text", "")
        lines.append(f"Section {i} — {heading}")
        lines.append(text)
        lines.append("")
    return "\n".join(lines).strip()


def _parse_response(raw: str) -> list[SceneItem]:
    """Validate and parse the LLM JSON string into ``SceneItem`` objects."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Scene agent returned non-JSON content: {exc}\n\nRaw:\n{raw[:500]}"
        ) from exc

    if isinstance(data, dict):
        array = next((v for v in data.values() if isinstance(v, list)), None)
        if array is None:
            raise ValueError(
                f"Scene agent returned a JSON object with no array value. "
                f"Keys: {list(data.keys())}"
            )
        data = array

    if not isinstance(data, list):
        raise ValueError(f"Scene agent output is not a JSON array. Got: {type(data)}")

    scenes: list[SceneItem] = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            logger.warning("scenes[{}] is not an object — skipped", i)
            continue

        scene_title = str(item.get("scene_title", f"Scene {i + 1}")).strip()
        raw_subscenes = item.get("subscenes", [])
        if not isinstance(raw_subscenes, list):
            logger.warning("scenes[{}] has no subscenes array — skipped", i)
            continue

        subscenes: list[SubSceneItem] = []
        for j, sub in enumerate(raw_subscenes):
            if not isinstance(sub, dict):
                logger.warning("scenes[{}].subscenes[{}] is not an object — skipped", i, j)
                continue
            text = str(sub.get("text", "")).strip()
            visual = str(sub.get("visual_description", "")).strip()
            if not text or not visual:
                logger.warning(
                    "scenes[{}].subscenes[{}] missing text or visual_description — skipped",
                    i, j,
                )
                continue
            subscenes.append(SubSceneItem(text=text, visual_description=visual))

        if not subscenes:
            logger.warning("scenes[{}] '{}' has no valid subscenes — skipped", i, scene_title)
            continue

        scenes.append(SceneItem(scene_title=scene_title, subscenes=subscenes))

    if not scenes:
        raise ValueError("Scene agent returned no valid scenes after parsing")

    return scenes

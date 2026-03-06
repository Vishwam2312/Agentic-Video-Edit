"""
agents/animation_agent.py
──────────────────────────
Converts a scene or subscene description into a runnable Manim (Community
Edition) Python animation script using an OpenAI-compatible LLM.

The generated code can be executed via:
    manim -pql <file>.py SceneAnimation
to produce a short video segment.

Both scene-level and subscene-level dicts are accepted:

  Scene dict keys:    narration_text, visual_description, focus_words, index
  Subscene dict keys: text, visual_description, subscene_id  (+ optional index)
"""

from __future__ import annotations

import re

from loguru import logger
from openai import AsyncOpenAI

from backend.config import settings


# ── System prompt ─────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are an expert Manim (Community Edition v0.18+) programmer who creates \
short, self-contained educational animations.

Given a scene description, narration text, and focus keywords, write a \
complete, runnable Manim Python script.

Rules:
1. The script must be importable standalone — include all necessary imports \
   at the top (`from manim import *`).
2. Define exactly ONE Scene subclass named `SceneAnimation`.
3. Implement the `construct(self)` method with the full animation.
4. Keep total run time under 20 seconds (short, punchy scenes).
5. Use high-quality visuals: text, shapes, arrows, color highlights, \
   Write/FadeIn/Transform animations.
6. Highlight focus_words on screen using colored Text or MathTex.
7. End with a brief hold: `self.wait(1)`.
8. Output ONLY the raw Python code — no markdown fences, no explanation, \
   no prose before or after the code.
9. The code must be syntactically correct Python that Manim can execute \
   without modification.

Example structure:
from manim import *

class SceneAnimation(Scene):
    def construct(self):
        title = Text("My Title", font_size=36)
        self.play(Write(title))
        self.wait(1)
"""

_MAX_CHARS = 2_000   # scene descriptions are short; keep prompt compact


# ── Public API ────────────────────────────────────────────────────────────────

async def generate_animation_code(
    scene: dict,
    *,
    model: str | None = None,
) -> str:
    """
    Generate a Manim Python animation script for a single scene or subscene.

    Parameters
    ----------
    scene:
        Scene dict with keys:
          - ``narration_text`` (str)  — spoken text
          - ``visual_description`` (str) — what to animate on screen
          - ``focus_words`` (list[str]) — key terms to highlight
          - ``index`` (int, optional) — 0-based position

        **Or** a subscene dict with keys:
          - ``text`` (str) — spoken text (mapped automatically to narration_text)
          - ``visual_description`` (str)
          - ``subscene_id`` (str, optional) — used in log messages
          - ``index`` (int, optional)
    model:
        Optional model override; falls back to ``settings.openai_model``.

    Returns
    -------
    str
        Complete, runnable Manim Python source code.

    Raises
    ------
    ValueError
        If the LLM returns an empty response or strips all code.
    openai.OpenAIError
        Propagated directly for upstream handling.
    """
    resolved_model = model or settings.openai_model

    client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url or None,
    )

    # Normalise subscene dicts: map `text` → `narration_text`
    normalised = _normalise_input(scene)

    user_content = _build_user_prompt(normalised)
    logger.info(
        "Requesting Manim code — model={} scene_index={} subscene_id={}",
        resolved_model,
        normalised.get("index", "?"),
        normalised.get("subscene_id", "—"),
    )

    response = await client.chat.completions.create(
        model=resolved_model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,   # low temp → more deterministic, syntactically stable code
    )

    raw = (response.choices[0].message.content or "").strip()
    logger.debug("Animation LLM response — {} chars", len(raw))

    code = _clean_code(raw)
    if not code:
        raise ValueError("LLM returned an empty animation script")

    return code


# ── Internal helpers ──────────────────────────────────────────────────────────
def _normalise_input(data: dict) -> dict:
    """
    Accept both scene dicts (``narration_text`` key) and subscene dicts
    (``text`` key) and return a unified dict that always has
    ``narration_text``, ``visual_description``, ``focus_words``, and ``index``.
    """
    if "narration_text" not in data and "text" in data:
        data = {
            **data,
            "narration_text": data["text"],
        }
    return data
def _build_user_prompt(scene: dict) -> str:
    narration = str(scene.get("narration_text", "")).strip()[:_MAX_CHARS]
    visual = str(scene.get("visual_description", "")).strip()[:_MAX_CHARS]
    focus = scene.get("focus_words", [])
    focus_str = ", ".join(str(w) for w in focus) if focus else "none"
    index = scene.get("index", 0)

    return (
        f"Scene {index + 1}\n\n"
        f"Narration text (spoken audio):\n{narration}\n\n"
        f"Visual description (what to animate):\n{visual}\n\n"
        f"Focus words to highlight on screen: {focus_str}\n\n"
        "Write the complete Manim animation script for this scene."
    )


def _clean_code(raw: str) -> str:
    """Strip markdown fences that some models wrap code in."""
    # Remove ```python ... ``` or ``` ... ```
    fenced = re.sub(
        r"^```(?:python)?\s*\n?",
        "",
        raw.strip(),
        flags=re.IGNORECASE,
    )
    fenced = re.sub(r"\n?```\s*$", "", fenced.strip())
    return fenced.strip()

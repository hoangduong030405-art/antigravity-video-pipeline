"""Local AI-style planning layer for the video pipeline."""

from __future__ import annotations

import re
from typing import Any


class PlanError(ValueError):
    """Raised when story planning fails."""


def _clean_sentence(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def generate_storyboard(prompt: str, scene_count: int = 5, duration: float = 20, style: str = "cinematic") -> dict[str, Any]:
    """Create a richer storyboard using lightweight local heuristics."""
    if not prompt or not _clean_sentence(prompt):
        raise PlanError("Prompt cannot be empty.")
    if not 1 <= scene_count <= 12:
        raise PlanError("Scene count must be between 1 and 12.")
    if duration <= 0:
        raise PlanError("Duration must be greater than zero.")

    cleaned = _clean_sentence(prompt)
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\s*;\s*", cleaned) if s.strip()]
    if not sentences:
        sentences = [cleaned]
    captions = (sentences * ((scene_count // len(sentences)) + 1))[:scene_count]
    scene_duration = duration / scene_count
    scenes = []
    for index, sentence in enumerate(captions, start=1):
        title = sentence[:48].rstrip(" .,;:!?") or f"Scene {index}"
        scenes.append(
            {
                "title": title,
                "subtitle": sentence,
                "duration": round(scene_duration, 3),
                "visual": _visual_prompt(sentence, index, style),
            }
        )

    return {
        "title": f"{style.title()} Story",
        "style": style,
        "scenes": scenes,
    }


def _visual_prompt(sentence: str, index: int, style: str) -> str:
    mood = {
        "cinematic": "cinematic lighting, atmospheric gradients, high contrast, dramatic framing",
        "dreamy": "soft pastel colors, airy fog, warm cinematic glow, elegant composition",
        "neon": "vivid neon accents, cyberpunk palette, glossy reflections, futuristic city mood",
    }.get(style, "cinematic lighting, rich compositional depth")
    return f"Scene {index}: {sentence[:100]} — {mood}."

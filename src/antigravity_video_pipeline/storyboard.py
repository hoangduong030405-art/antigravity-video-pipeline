"""Simple prompt-to-storyboard conversion and validation."""

from __future__ import annotations

import re
from typing import Any


class StoryboardError(ValueError):
    """Raised when storyboard input is invalid."""


def split_prompt(prompt: str) -> list[str]:
    """Split prose into useful scene-sized chunks, preserving punctuation."""
    cleaned = " ".join(prompt.strip().split())
    if not cleaned:
        raise StoryboardError("Prompt cannot be empty.")
    chunks = [part.strip() for part in re.split(r"(?<=[.!?])\s+|\s*;\s*", cleaned) if part.strip()]
    return chunks or [cleaned]


def storyboard_from_prompt(prompt: str, scene_count: int = 5, duration: float = 20) -> dict[str, Any]:
    if not 1 <= scene_count <= 12:
        raise StoryboardError("Scene count must be between 1 and 12.")
    if duration <= 0:
        raise StoryboardError("Duration must be greater than zero.")

    chunks = split_prompt(prompt)
    selected = (chunks + chunks[-1:] * scene_count)[:scene_count]
    scene_duration = duration / scene_count
    scenes = [
        {
            "title": _title_for(chunk),
            "subtitle": chunk,
            "duration": round(scene_duration, 3),
        }
        for chunk in selected
    ]
    return {"title": _title_for(chunks[0]), "scenes": scenes}


def _title_for(text: str, limit: int = 48) -> str:
    text = text.strip().rstrip(".!?;:")
    if len(text) <= limit:
        return text
    shortened = text[: limit - 1].rsplit(" ", 1)[0].strip()
    return (shortened or text[: limit - 1]).rstrip(".,:;") + "…"


def validate_storyboard(data: dict[str, Any], default_duration: float) -> list[dict[str, Any]]:
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise StoryboardError("Storyboard must contain a non-empty 'scenes' list.")
    normalized: list[dict[str, Any]] = []
    for index, scene in enumerate(scenes, start=1):
        if not isinstance(scene, dict):
            raise StoryboardError(f"Scene {index} must be an object.")
        title = str(scene.get("title", "")).strip()
        subtitle = str(scene.get("subtitle", "")).strip()
        if not title and not subtitle:
            raise StoryboardError(f"Scene {index} needs a title or subtitle.")
        try:
            scene_duration = float(scene.get("duration", default_duration / len(scenes)))
        except (TypeError, ValueError) as exc:
            raise StoryboardError(f"Scene {index} has an invalid duration.") from exc
        if scene_duration <= 0:
            raise StoryboardError(f"Scene {index} duration must be greater than zero.")
        normalized.append({
            "title": title or subtitle,
            "subtitle": subtitle,
            "duration": scene_duration,
        })
    return normalized

"""Prompt-to-video starter pipeline."""

__version__ = "0.1.0"

from .ai import generate_storyboard
from .renderer import RenderError, render_video

__all__ = ["__version__", "generate_storyboard", "render_video", "RenderError"]

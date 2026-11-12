"""Core rendering functionality for the antigravity video pipeline."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from .ai import PlanError
from .storyboard import StoryboardError, validate_storyboard


class RenderError(RuntimeError):
    """Raised when video rendering cannot complete."""


PALETTES = [((17, 24, 39), (37, 99, 235)), ((19, 78, 74), (13, 148, 136)),
            ((76, 29, 149), (192, 38, 211)), ((124, 45, 18), (234, 88, 12)),
            ((30, 41, 59), (8, 145, 178)), ((63, 63, 70), (101, 163, 13))]


def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = (
        ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"]
        if bold else
        ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:/Windows/Fonts/arial.ttf"]
    )
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _draw_card(title: str, subtitle: str, width: int, height: int, index: int) -> Image.Image:
    start, end = PALETTES[index % len(PALETTES)]
    image = Image.new("RGB", (width, height))
    pixels = image.load()
    for y in range(height):
        for x in range(width):
            amount = min(1.0, max(0.0, (x / max(1, width - 1) * 0.65 + y / max(1, height - 1) * 0.35)))
            pixels[x, y] = tuple(round(start[c] * (1 - amount) + end[c] * amount) for c in range(3))

    draw = ImageDraw.Draw(image, "RGBA")
    draw.ellipse((width * 0.68, -height * 0.45, width * 1.18, height * 0.55), outline=(255, 255, 255, 35), width=max(2, width // 400))
    draw.ellipse((width * 0.75, -height * 0.34, width * 1.1, height * 0.36), outline=(255, 255, 255, 25), width=max(2, width // 500))
    margin = int(width * 0.09)
    title_font = _font(max(24, int(height * 0.075)), bold=True)
    subtitle_font = _font(max(16, int(height * 0.032)))
    title_lines = _wrap_text(draw, title, title_font, width - 2 * margin)[:3]
    subtitle_lines = _wrap_text(draw, subtitle, subtitle_font, width - 2 * margin)[:4]
    title_line_height = int(title_font.size * 1.22)
    subtitle_line_height = int(subtitle_font.size * 1.5)
    content_height = len(title_lines) * title_line_height + (int(height * 0.035) if subtitle_lines else 0) + len(subtitle_lines) * subtitle_line_height
    y = max(int(height * 0.24), (height - content_height) // 2)
    draw.rounded_rectangle((margin, y - 28, margin + 94, y - 17), radius=5, fill=(255, 255, 255, 210))
    y += 10
    for line in title_lines:
        draw.text((margin, y), line, font=title_font, fill=(255, 255, 255), stroke_width=1, stroke_fill=(0, 0, 0, 30))
        y += title_line_height
    if subtitle_lines:
        y += int(height * 0.035)
        for line in subtitle_lines:
            draw.text((margin, y), line, font=subtitle_font, fill=(235, 242, 255))
            y += subtitle_line_height
    return image


def render_video(
    script: dict[str, Any], output: Path, duration: float = 20, width: int = 1280,
    height: int = 720, fps: int = 30, audio: Path | None = None, transition: str = "fade"
) -> Path:
    if duration <= 0:
        raise RenderError("Duration must be greater than zero.")
    if width < 320 or height < 240 or width % 2 or height % 2:
        raise RenderError("Width and height must be even numbers (at least 320x240) for MP4 output.")
    if not 1 <= fps <= 60:
        raise RenderError("FPS must be between 1 and 60.")
    if transition not in {"none", "fade"}:
        raise RenderError("Transition must be either 'none' or 'fade'.")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RenderError("FFmpeg was not found. Install FFmpeg and make sure 'ffmpeg' is on PATH.")
    if audio is not None and not audio.is_file():
        raise RenderError(f"Audio file does not exist: {audio}")
    try:
        scenes = validate_storyboard(script, duration)
    except StoryboardError:
        raise

    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    scene_total = sum(scene["duration"] for scene in scenes)
    with tempfile.TemporaryDirectory(prefix="ag-video-") as temp_dir:
        work = Path(temp_dir)
        concat_file = work / "concat.txt"
        lines: list[str] = []
        for index, scene in enumerate(scenes):
            image_path = work / f"scene-{index:03d}.png"
            _draw_card(scene["title"], scene["subtitle"], width, height, index).save(image_path)
            safe_path = image_path.as_posix().replace("'", "'\\''")
            lines.extend([f"file '{safe_path}'", f"duration {scene['duration']:.6f}"])
        last_path = (work / f"scene-{len(scenes) - 1:03d}.png").as_posix().replace("'", "'\\''")
        lines.append(f"file '{last_path}'")
        concat_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file)]
        if audio is not None:
            command.extend(["-i", str(audio.resolve()), "-map", "0:v:0", "-map", "1:a:0", "-c:a", "aac", "-shortest"])
        else:
            command.extend(["-map", "0:v:0"])
        if transition == "fade":
            fade_in = 0.75
            fade_out = min(0.75, max(scene_total * 0.15, 0.5))
            command.extend(["-vf", f"fade=t=in:st=0:d={fade_in},fade=t=out:st={max(scene_total - fade_out, 0.1)}:d={fade_out}"])
        command.extend([
            "-vsync", "vfr", "-r", str(fps), "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", "-t", f"{scene_total:.6f}", str(output),
        ])
        try:
            result = subprocess.run(command, check=False, capture_output=True, text=True)
        except OSError as exc:
            raise RenderError(f"Could not start FFmpeg: {exc}") from exc
        if result.returncode != 0:
            detail = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "unknown FFmpeg error"
            raise RenderError(f"FFmpeg failed: {detail}")
    return output


__all__ = ["RenderError", "render_video"]

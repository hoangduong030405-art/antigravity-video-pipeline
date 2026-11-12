"""Command-line interface for the video pipeline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .renderer import RenderError, render_video
from .storyboard import StoryboardError, storyboard_from_prompt


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ag-video",
        description="Turn a text prompt or storyboard JSON into an MP4 title-card video.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    storyboard = commands.add_parser("storyboard", help="Create an editable storyboard JSON from a prompt.")
    storyboard.add_argument("--prompt", required=True, help="Description or short story for the video.")
    storyboard.add_argument("--output", type=Path, required=True, help="Path for the storyboard JSON.")
    storyboard.add_argument("--scenes", type=int, default=5, help="Number of storyboard scenes (1-12).")
    storyboard.add_argument("--duration", type=float, default=20, help="Total video duration in seconds.")

    render = commands.add_parser("render", help="Render a prompt or storyboard JSON to MP4.")
    source = render.add_mutually_exclusive_group(required=True)
    source.add_argument("--prompt", help="Description or short story for the video.")
    source.add_argument("--script", type=Path, help="Storyboard JSON file.")
    render.add_argument("--output", type=Path, required=True, help="Output MP4 path.")
    render.add_argument("--scenes", type=int, default=5, help="Scene count for prompt input (1-12).")
    render.add_argument("--duration", type=float, default=20, help="Total duration in seconds.")
    render.add_argument("--width", type=int, default=1280, help="Video width in pixels.")
    render.add_argument("--height", type=int, default=720, help="Video height in pixels.")
    render.add_argument("--fps", type=int, default=30, help="Frames per second.")
    render.add_argument("--audio", type=Path, help="Optional audio file to mux into the video.")
    return parser


def _write_storyboard(args: argparse.Namespace) -> None:
    data = storyboard_from_prompt(args.prompt, args.scenes, args.duration)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Storyboard written to {args.output}")


def _read_script(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StoryboardError(f"Could not read storyboard JSON '{path}': {exc}") from exc
    if not isinstance(data, dict):
        raise StoryboardError("Storyboard must be a JSON object.")
    return data


def main() -> None:
    args = _parser().parse_args()
    try:
        if args.command == "storyboard":
            _write_storyboard(args)
            return
        script = (
            _read_script(args.script)
            if args.script
            else storyboard_from_prompt(args.prompt, args.scenes, args.duration)
        )
        output = render_video(
            script=script,
            output=args.output,
            duration=args.duration,
            width=args.width,
            height=args.height,
            fps=args.fps,
            audio=args.audio,
        )
        print(f"Video rendered: {output}")
    except (RenderError, StoryboardError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()

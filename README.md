# Antigravity Video Pipeline

A small, local-first starter app that turns a text prompt into a simple storyboard and renders it as an MP4 using FFmpeg. It creates clean, animated-looking title cards from text and procedural backgrounds; it does **not** call an image or video generation model yet.

## Requirements

- Python 3.10+
- FFmpeg installed and available on `PATH` (`ffmpeg -version`)

## Install

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e .
```

## Quick start

Render a video directly from a prompt:

```bash
ag-video render --prompt "A quiet morning in a Japanese garden. Sunlight touches the pond. A heron takes flight." --output output/garden.mp4
```

Control the length, number of scenes, format, or add an audio track:

```bash
ag-video render \
  --prompt "A short story about exploring Mars and finding signs of water" \
  --output output/mars.mp4 \
  --duration 24 --scenes 4 --width 1920 --height 1080 --fps 30 \
  --audio music.mp3
```

Generate and edit a storyboard JSON before rendering:

```bash
ag-video storyboard --prompt "A cozy coffee shop on a rainy day" --output project.json
ag-video render --script project.json --output output/coffee.mp4
```

A script can also be written by hand:

```json
{
  "title": "A Small Adventure",
  "scenes": [
    {"title": "The Journey Begins", "subtitle": "One step beyond the familiar."},
    {"title": "A New Discovery", "subtitle": "The world is bigger than it seems."}
  ]
}
```

If a script has no per-scene `duration`, the requested `--duration` is divided evenly across its scenes. Generated prompt storyboards include durations automatically. Supported audio formats depend on the FFmpeg build. Audio is optional; without it, the video is silent.

## Development

```bash
python -m unittest discover -s tests -v
```

## Current scope

- Prompt-to-storyboard using a lightweight sentence-based heuristic.
- Readable title cards with procedural color backgrounds.
- MP4 rendering through FFmpeg; optional user-provided audio.
- No external API keys, model training, generated imagery, or automatic voiceover.

The project is intentionally modular so an image-generation, LLM storyboard, or narration provider can be added later without changing the renderer's basic interface.

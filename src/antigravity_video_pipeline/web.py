"""Minimal web UI for local prompt-to-video generation."""

from __future__ import annotations

import html
import os
from pathlib import Path

from flask import Flask, render_template_string, request

from .ai import generate_storyboard
from .renderer import RenderError, render_video


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["OUTPUT_DIR"] = Path(os.environ.get("AG_VIDEO_OUTPUT_DIR", "output"))

    index_template = """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <title>Antigravity Video Generator</title>
        <style>
          body { font-family: sans-serif; background: #07111f; color: #e5eefb; margin: 0; padding: 48px; }
          .container { max-width: 980px; margin: 0 auto; }
          .panel { background: rgba(15, 23, 42, 0.9); border: 1px solid #23314d; border-radius: 18px; padding: 26px; box-shadow: 0 20px 60px rgba(0,0,0,0.28); }
          textarea, input, select { width: 100%; box-sizing: border-box; margin-top: 8px; padding: 14px 16px; border-radius: 10px; border: 1px solid #365079; background: #0b1729; color: #e5eefb; }
          button { margin-top: 16px; background: linear-gradient(135deg, #4f46e5, #8b5cf6); color: white; border: none; border-radius: 12px; padding: 14px 18px; cursor: pointer; font-size: 16px; }
          label { display: block; margin-top: 18px; font-weight: 600; }
          .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; }
          .result { margin-top: 22px; white-space: pre-wrap; background: #0a1322; border: 1px solid #23314d; border-radius: 12px; padding: 16px; }
          a { color: #8ec5ff; }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="panel">
            <h1>Antigravity Video Generator</h1>
            <form method="post" action="/generate">
              <label>Prompt
                <textarea name="prompt" rows="5" placeholder="Describe a cinematic scene or story..."></textarea>
              </label>
              <div class="grid">
                <label>Scenes
                  <input type="number" name="scenes" min="1" max="12" value="5" />
                </label>
                <label>Duration (s)
                  <input type="number" name="duration" min="5" max="120" value="20" step="1" />
                </label>
                <label>Style
                  <select name="style">
                    <option value="cinematic">Cinematic</option>
                    <option value="dreamy">Dreamy</option>
                    <option value="neon">Neon</option>
                  </select>
                </label>
              </div>
              <button type="submit">Generate video</button>
            </form>
            {% if result %}
              <div class="result">
                <h2>Result</h2>
                <pre>{{ result }}</pre>
                {% if output_url %}
                  <p><a href="{{ output_url }}" target="_blank" rel="noreferrer">Open generated MP4</a></p>
                {% endif %}
              </div>
            {% endif %}
          </div>
        </div>
      </body>
    </html>
    """

    @app.get("/")
    def index():
        return render_template_string(index_template, result=None, output_url=None)

    @app.post("/generate")
    def generate():
        prompt = request.form.get("prompt", "").strip()
        scenes = max(1, min(12, int(request.form.get("scenes", "5") or 5)))
        duration = max(5, float(request.form.get("duration", "20") or 20.0))
        style = request.form.get("style", "cinematic")

        if not prompt:
            return render_template_string(index_template, result="Please enter a prompt first.", output_url=None)

        try:
            storyboard = generate_storyboard(prompt, scenes, duration, style=style)
            output_dir = app.config["OUTPUT_DIR"]
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "web_preview.mp4"
            render_video(storyboard, output=output_path, duration=duration, transition="fade")
            url = f"/static/{output_path.name}"
            return render_template_string(index_template, result=html.escape(str(storyboard)), output_url=url)
        except (RenderError, ValueError) as exc:
            return render_template_string(index_template, result=f"Error: {exc}", output_url=None)

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=8000, debug=False)

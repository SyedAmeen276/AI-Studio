import argparse
import re
import subprocess
import textwrap
from pathlib import Path

from app.video.config import (
    VIDEO_OUTPUT_DIR,
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    VIDEO_FPS,
    BACKGROUND_COLOR,
    FONT_PATH,
)

from app.video.captions import generate_srt


def escape_filter_path(path):
    return str(path.resolve()).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def run_command(command):
    print("\nRendering video...")

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError("Video rendering failed.")

    print("Rendering completed.")


def render_video(script_path, audio_path):
    import json

    script_path = Path(script_path)
    audio_path = Path(audio_path)

    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    if not audio_path.exists():
        raise FileNotFoundError(f"Audio not found: {audio_path}")

    with script_path.open("r", encoding="utf-8") as file:
        script = json.load(file)

    title = script.get("title", "AI Content Studio")

    output_dir = VIDEO_OUTPUT_DIR / script_path.parent.name
    output_dir.mkdir(parents=True, exist_ok=True)

    title_file = output_dir / "title.txt"

    title_file.write_text(
        textwrap.fill(title, width=30),
        encoding="utf-8"
    )

    manifest_path = audio_path.parent / "manifest.json"
    captions_path = output_dir / "captions.srt"

    if not manifest_path.exists():
        raise FileNotFoundError(
            f"TTS manifest not found: {manifest_path}"
        )

    generate_srt(
        script_path,
        manifest_path,
        captions_path
    )

    output_file = output_dir / "video.mp4"

    title_path = escape_filter_path(title_file)
    captions_filter_path = escape_filter_path(captions_path)

    # Only two visual layers:
    # 1. Main title
    # 2. Dynamic narration captions
    video_filter = (
        f"drawtext=fontfile={FONT_PATH}:"
        f"textfile='{title_path}':"
        "fontcolor=white:"
        "fontsize=72:"
        "line_spacing=18:"
        "x=(w-text_w)/2:"
        "y=(h-text_h)/2-100,"
        f"subtitles='{captions_filter_path}':"
        "force_style='FontName=DejaVu Sans,"
        "FontSize=22,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "BorderStyle=1,"
        "Outline=2,"
        "Shadow=1,"
        "Alignment=2,"
        "MarginV=65'"
    )

    command = [
        "ffmpeg",
        "-y",
        "-f", "lavfi",
        "-i",
        f"color=c={BACKGROUND_COLOR}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:r={VIDEO_FPS}",
        "-i", str(audio_path),
        "-vf", video_filter,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(output_file),
    ]

    print(f"Title: {title}")
    print(f"Audio: {audio_path}")
    print(f"Captions: {captions_path}")

    run_command(command)

    print(f"\nVideo created: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate a narrated video with captions."
    )

    parser.add_argument("--script", required=True)
    parser.add_argument("--audio", required=True)

    args = parser.parse_args()

    render_video(args.script, args.audio)


if __name__ == "__main__":
    main()
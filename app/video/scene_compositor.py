import argparse
import json
import subprocess

from pathlib import Path

from app.video.config import (
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    VIDEO_FPS,
    BACKGROUND_COLOR,
)

from app.video.captions import generate_srt


def run_command(command):
    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError("Video composition failed.")

    print("Video composition completed.")


def escape_filter_path(path):
    return (
        str(Path(path).resolve())
        .replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
    )


def compose_video(
    scene_plan_path,
    animation_dir,
    audio_path,
    captions_path,
    output_path
):
    with open(
        scene_plan_path,
        "r",
        encoding="utf-8"
    ) as file:
        plan = json.load(file)

    scenes = plan["scenes"]

    total_duration = float(
        plan["total_duration_seconds"]
    )

    animation_dir = Path(animation_dir)
    audio_path = Path(audio_path)
    output_path = Path(output_path)

    if not audio_path.exists():
        raise FileNotFoundError(audio_path)

    if not scenes:
        raise ValueError("Scene plan contains no scenes.")

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel", "error",

        "-f", "lavfi",
        "-i",
        (
            f"color=c={BACKGROUND_COLOR}:"
            f"s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:"
            f"r={VIDEO_FPS}:"
            f"d={total_duration}"
        )
    ]

    # Add scene video inputs.
    for scene in scenes:
        scene_number = scene["scene_number"]
        scene_name = scene["name"]

        clip_path = (
            animation_dir /
            f"{scene_number:02d}_{scene_name}.mp4"
        )

        if not clip_path.exists():
            raise FileNotFoundError(
                f"Missing animated scene: {clip_path}"
            )

        command.extend([
            "-i",
            str(clip_path)
        ])

    # Add narration.
    command.extend([
        "-i",
        str(audio_path)
    ])

    filters = []

    previous_video = "0:v"

    # Place each scene on its planned timeline.
    for index, scene in enumerate(scenes, start=1):

        start = float(scene["start_time"])
        end = float(scene["end_time"])

        scene_input = f"{index}:v"
        prepared = f"scene{index}"
        output_label = f"composed{index}"

        filters.append(
            f"[{scene_input}]"
            f"setpts=PTS-STARTPTS+{start}/TB"
            f"[{prepared}]"
        )

        filters.append(
            f"[{previous_video}]"
            f"[{prepared}]"
            f"overlay=0:0:"
            f"enable='between(t,{start},{end})':"
            f"eof_action=pass:"
            f"shortest=0"
            f"[{output_label}]"
        )

        previous_video = output_label

    # Add subtitles.
    subtitle_path = escape_filter_path(
        captions_path
    )

    filters.append(
        f"[{previous_video}]"
        f"subtitles='{subtitle_path}':"
        "force_style='"
        "FontName=DejaVu Sans,"
        "FontSize=22,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "BorderStyle=1,"
        "Outline=2,"
        "Shadow=1,"
        "Alignment=2,"
        "MarginV=65"
        "'"
        "[finalvideo]"
    )

    filter_complex = ";".join(filters)

    audio_input_index = len(scenes) + 1

    command.extend([
        "-filter_complex",
        filter_complex,

        "-map",
        "[finalvideo]",

        "-map",
        f"{audio_input_index}:a:0",

        "-t",
        str(total_duration),

        "-c:v",
        "libx264",

        "-preset",
        "ultrafast",

        "-crf",
        "20",

        "-pix_fmt",
        "yuv420p",

        "-c:a",
        "aac",

        "-b:a",
        "192k",

        "-movflags",
        "+faststart",

        str(output_path)
    ])

    print(f"Scenes: {len(scenes)}")
    print(f"Duration: {total_duration:.2f}s")
    print(f"Narration: {audio_path}")
    print(f"Output: {output_path}")

    run_command(command)

    print(f"\nFinal video: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Compose animated scenes into a narrated video."
    )

    parser.add_argument("--script", required=True)
    parser.add_argument("--scene-plan", required=True)
    parser.add_argument("--animation-dir", required=True)
    parser.add_argument("--audio", required=True)
    parser.add_argument("--captions", required=True)
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    # Generate subtitles using the existing caption engine.
    audio_path = Path(args.audio)

    manifest_path = (
        audio_path.parent / "manifest.json"
    )

    captions_path = Path(args.captions)

    generate_srt(
        args.script,
        manifest_path,
        captions_path
    )

    compose_video(
        args.scene_plan,
        args.animation_dir,
        audio_path,
        captions_path,
        args.output
    )


if __name__ == "__main__":
    main()
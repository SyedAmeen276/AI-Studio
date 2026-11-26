import argparse
import json
import subprocess

from pathlib import Path


DEFAULT_FPS = 30
DEFAULT_WIDTH = 1920
DEFAULT_HEIGHT = 1080


def run_command(command):
    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError("Animation rendering failed.")

    return result


def get_frame_count(duration, fps):
    return max(1, round(duration * fps))


def build_animation_filter(scene_number, fps):
    """
    Generate a smooth camera zoom animation.

    Alternates between gentle horizontal camera drift
    directions while maintaining a centered zoom.
    """

    direction = 1 if scene_number % 2 else -1

    zoom = "min(1+0.0004*on,1.08)"

    x = (
        f"(iw-iw/zoom)/2"
        f"+{direction}*0.08*(iw-iw/zoom)"
    )

    y = "(ih-ih/zoom)/2"

    return (
        f"zoompan="
        f"z='{zoom}':"
        f"x='{x}':"
        f"y='{y}':"
        f"d=1:"
        f"s={DEFAULT_WIDTH}x{DEFAULT_HEIGHT}:"
        f"fps={fps},"
        f"format=yuv420p"
    )


def animate_scene(scene, image_dir, output_dir, fps):
    scene_number = scene["scene_number"]
    scene_name = scene["name"]
    duration = float(scene["duration"])

    image_path = (
        image_dir /
        f"{scene_number:02d}_{scene_name.replace('_', '-')}.png"
    )

    # The filename generator converts underscores to hyphens.
    # Hook and section names already use compatible filenames.
    if not image_path.exists():
        raise FileNotFoundError(
            f"Scene image not found: {image_path}"
        )

    output_path = (
        output_dir /
        f"{scene_number:02d}_{scene_name}.mp4"
    )

    frames = get_frame_count(duration, fps)

    video_filter = build_animation_filter(
        scene_number,
        fps
    )

    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel", "error",

        "-loop", "1",
        "-framerate", str(fps),
        "-i", str(image_path),

        "-vf", video_filter,

        "-frames:v", str(frames),

        "-an",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",

        "-movflags", "+faststart",

        str(output_path)
    ]

    print(
        f"Animating scene {scene_number}: "
        f"{scene_name} ({duration:.2f}s)"
    )

    run_command(command)

    return {
        "scene_number": scene_number,
        "name": scene_name,
        "image": str(image_path),
        "video": str(output_path),
        "duration": duration,
        "fps": fps,
        "frames": frames
    }


def generate_animations(
    scene_plan_path,
    image_dir,
    output_dir,
    fps=DEFAULT_FPS
):
    with open(
        scene_plan_path,
        "r",
        encoding="utf-8"
    ) as file:
        scene_plan = json.load(file)

    image_dir = Path(image_dir)
    output_dir = Path(output_dir)

    if not image_dir.exists():
        raise FileNotFoundError(
            f"Image directory not found: {image_dir}"
        )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    results = []

    for scene in scene_plan["scenes"]:
        result = animate_scene(
            scene,
            image_dir,
            output_dir,
            fps
        )

        results.append(result)

    manifest = {
        "title": scene_plan["title"],
        "resolution": f"{DEFAULT_WIDTH}x{DEFAULT_HEIGHT}",
        "fps": fps,
        "total_scenes": len(results),
        "scenes": results
    }

    manifest_path = output_dir / "animation_manifest.json"

    with open(
        manifest_path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            manifest,
            file,
            indent=4
        )

    print("\nAnimation generation completed.")
    print(f"Generated clips: {len(results)}")
    print(f"Manifest: {manifest_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Animate educational video scenes."
    )

    parser.add_argument(
        "--scene-plan",
        required=True
    )

    parser.add_argument(
        "--image-dir",
        required=True
    )

    parser.add_argument(
        "--output-dir",
        required=True
    )

    parser.add_argument(
        "--fps",
        type=int,
        default=DEFAULT_FPS
    )

    args = parser.parse_args()

    generate_animations(
        args.scene_plan,
        args.image_dir,
        args.output_dir,
        args.fps
    )


if __name__ == "__main__":
    main()
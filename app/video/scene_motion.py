import argparse
import json
import math
import subprocess

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


WIDTH = 1920
HEIGHT = 1080
FPS = 30

BACKGROUND = (13, 20, 34)
PANEL = (25, 36, 55)
BLUE = (65, 160, 255)
GREEN = (70, 200, 140)
ORANGE = (255, 170, 80)
WHITE = (245, 247, 250)
MUTED = (160, 175, 195)

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")


def font(size, bold=False):
    filename = (
        "DejaVuSans-Bold.ttf"
        if bold else "DejaVuSans.ttf"
    )

    return ImageFont.truetype(
        str(FONT_DIR / filename),
        size
    )


def ease_out(value):
    value = max(0.0, min(1.0, value))
    return 1 - (1 - value) ** 3


def interpolate(start, end, progress):
    return start + (end - start) * progress


def draw_header(draw, heading):
    draw.text(
        (100, 65),
        heading,
        font=font(54, True),
        fill=WHITE
    )

    draw.line(
        (100, 145, 1820, 145),
        fill=BLUE,
        width=4
    )


def draw_card(
    draw,
    x,
    y,
    width,
    height,
    title,
    description,
    color=BLUE,
    opacity=1.0
):
    opacity = max(0.0, min(1.0, opacity))

    if opacity <= 0:
        return

    fill = tuple(
        int(BACKGROUND[i] * (1 - opacity) +
            PANEL[i] * opacity)
        for i in range(3)
    )

    draw.rounded_rectangle(
        (x, y, x + width, y + height),
        radius=24,
        fill=fill,
        outline=color,
        width=5
    )

    if opacity > 0.65:
        draw.text(
            (x + 30, y + 30),
            title,
            font=font(34, True),
            fill=WHITE
        )

        draw.text(
            (x + 30, y + 95),
            description,
            font=font(23),
            fill=MUTED
        )


def draw_arrow(draw, start, end, progress, color=BLUE):
    progress = max(0.0, min(1.0, progress))

    if progress <= 0:
        return

    current_end = (
        int(interpolate(start[0], end[0], progress)),
        int(interpolate(start[1], end[1], progress))
    )

    draw.line(
        [start, current_end],
        fill=color,
        width=9
    )

    if progress >= 1.0:
        angle = math.atan2(
            end[1] - start[1],
            end[0] - start[0]
        )

        length = 25
        spread = math.pi / 6

        left = (
            end[0] - length * math.cos(angle - spread),
            end[1] - length * math.sin(angle - spread)
        )

        right = (
            end[0] - length * math.cos(angle + spread),
            end[1] - length * math.sin(angle + spread)
        )

        draw.polygon(
            [end, left, right],
            fill=color
        )


def draw_footer(draw, scene_name):
    draw.text(
        (100, 1000),
        f"AI CONTENT STUDIO  |  {scene_name}",
        font=font(22),
        fill=MUTED
    )


def architecture_frame(draw, heading, progress):
    draw_header(draw, heading)

    positions = [160, 765, 1370]

    components = [
        ("Docker CLI", "User commands"),
        ("Docker Engine", "Manages containers"),
        ("Container", "Runs applications")
    ]

    y = 390
    width = 390
    height = 180

    reveals = [
        ease_out((progress - 0.05) / 0.22),
        ease_out((progress - 0.30) / 0.22),
        ease_out((progress - 0.68) / 0.22)
    ]

    for index, (title, description) in enumerate(components):
        reveal = reveals[index]

        if reveal <= 0:
            continue

        offset = int(100 * (1 - reveal))

        draw_card(
            draw,
            positions[index],
            y + offset,
            width,
            height,
            title,
            description,
            GREEN if index == 2 else BLUE,
            reveal
        )

    draw_arrow(
        draw,
        (550, 480),
        (745, 480),
        ease_out((progress - 0.25) / 0.20)
    )

    draw_arrow(
        draw,
        (1155, 480),
        (1350, 480),
        ease_out((progress - 0.55) / 0.20)
    )


def layers_frame(draw, heading, progress):
    draw_header(draw, heading)

    layers = [
        ("Base image", ORANGE),
        ("Runtime and dependencies", BLUE),
        ("Application code", GREEN)
    ]

    x = 570
    y = 350

    # Build from bottom to top.
    for index, (label, color) in enumerate(layers):
        reveal = ease_out(
            (progress - index * 0.28) / 0.25
        )

        if reveal <= 0:
            continue

        target_y = y + (2 - index) * 145
        offset = int(180 * (1 - reveal))

        draw.rounded_rectangle(
            (
                x,
                target_y + offset,
                x + 780,
                target_y + 105 + offset
            ),
            radius=18,
            fill=PANEL,
            outline=color,
            width=5
        )

        if reveal > 0.65:
            draw.text(
                (x + 80, target_y + 30 + offset),
                label,
                font=font(30, True),
                fill=WHITE
            )

    if progress > 0.9:
        text = "A Docker image is composed of reusable layers"

        draw.text(
            (480, 850),
            text,
            font=font(30),
            fill=MUTED
        )


def container_frame(draw, heading, progress):
    draw_header(draw, heading)

    left_reveal = ease_out(progress / 0.35)
    right_reveal = ease_out((progress - 0.60) / 0.30)

    left_offset = int(120 * (1 - left_reveal))
    right_offset = int(120 * (1 - right_reveal))

    if left_reveal > 0:
        draw_card(
            draw,
            160 + left_offset,
            390,
            650,
            220,
            "Docker Image",
            "node:20-alpine",
            BLUE,
            left_reveal
        )

    draw_arrow(
        draw,
        (850, 500),
        (1060, 500),
        ease_out((progress - 0.35) / 0.25),
        GREEN
    )

    if right_reveal > 0:
        draw_card(
            draw,
            1100 + right_offset,
            390,
            650,
            220,
            "Running Container",
            "my-node-app",
            GREEN,
            right_reveal
        )

    if progress > 0.9:
        draw.text(
            (420, 760),
            "docker run --name my-node-app node:20-alpine",
            font=font(27),
            fill=ORANGE
        )


def summary_frame(draw, heading, progress):
    draw_header(draw, heading)

    cards = [
        ("CLI", "Accepts commands"),
        ("Engine", "Manages lifecycle"),
        ("Images", "Package applications"),
        ("Containers", "Run applications")
    ]

    positions = [
        (140, 350),
        (940, 350),
        (140, 600),
        (940, 600)
    ]

    for index, ((title, description), (x, y)) in enumerate(
        zip(cards, positions)
    ):
        reveal = ease_out(
            (progress - index * 0.20) / 0.22
        )

        offset = int(80 * (1 - reveal))

        draw_card(
            draw,
            x,
            y + offset,
            700,
            170,
            title,
            description,
            BLUE,
            reveal
        )


def generic_frame(draw, heading, narration, progress):
    draw_header(draw, heading)

    reveal = ease_out(progress / 0.4)

    draw_card(
        draw,
        200,
        320,
        1520,
        450,
        heading,
        "",
        BLUE,
        reveal
    )

    if reveal > 0.65:
        words = narration.split()
        lines = []

        for index in range(0, min(len(words), 48), 8):
            lines.append(" ".join(words[index:index + 8]))

        for index, line in enumerate(lines):
            draw.text(
                (280, 430 + index * 55),
                line,
                font=font(27),
                fill=WHITE
            )


def render_frame(scene, frame_number, total_frames):
    image = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        BACKGROUND
    )

    draw = ImageDraw.Draw(image)

    progress = (
        frame_number / max(1, total_frames - 1)
    )

    name = scene["name"]
    heading = scene["heading"]

    if name in ("hook", "introduction"):
        architecture_frame(
            draw,
            heading,
            progress
        )

    elif "image" in heading.lower() or "layer" in heading.lower():
        layers_frame(
            draw,
            heading,
            progress
        )

    elif "container" in heading.lower() or "running" in heading.lower():
        container_frame(
            draw,
            heading,
            progress
        )

    elif name == "conclusion":
        summary_frame(
            draw,
            heading,
            progress
        )

    else:
        generic_frame(
            draw,
            heading,
            scene.get("narration", ""),
            progress
        )

    draw_footer(draw, name)

    return image


def animate_scene(scene, output_dir, fps):
    duration = float(scene["duration"])

    total_frames = max(
        1,
        round(duration * fps)
    )

    output_path = (
        output_dir /
        f"{scene['scene_number']:02d}_{scene['name']}.mp4"
    )

    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel", "error",

        "-f", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-r", str(fps),
        "-i", "-",

        "-an",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",

        "-movflags", "+faststart",

        str(output_path)
    ]

    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE
    )

    try:
        for frame_number in range(total_frames):
            image = render_frame(
                scene,
                frame_number,
                total_frames
            )

            process.stdin.write(image.tobytes())

        process.stdin.close()

        return_code = process.wait()

        if return_code != 0:
            raise RuntimeError(
                f"FFmpeg failed for scene {scene['name']}"
            )

    except Exception:
        if process.poll() is None:
            process.kill()

        process.wait()
        raise

    print(
        f"Animated: {scene['name']} "
        f"({total_frames} frames)"
    )

    return output_path


def generate_animations(scene_plan_path, output_dir, fps):
    with open(
        scene_plan_path,
        "r",
        encoding="utf-8"
    ) as file:
        plan = json.load(file)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for scene in plan["scenes"]:
        animate_scene(
            scene,
            output_dir,
            fps
        )

    print("\nObject-level animation generation completed.")
    print(f"Output: {output_dir}")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--scene-plan", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--fps", type=int, default=FPS)

    args = parser.parse_args()

    generate_animations(
        args.scene_plan,
        args.output_dir,
        args.fps
    )


if __name__ == "__main__":
    main()
import argparse
import json
import math
import re

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH = 1920
HEIGHT = 1080

BACKGROUND = (13, 20, 34)
PANEL = (25, 36, 55)
ACCENT = (65, 160, 255)
WHITE = (245, 247, 250)
MUTED = (160, 175, 195)
GREEN = (70, 200, 140)
ORANGE = (255, 170, 80)

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")


def load_font(size, bold=False):
    filename = (
        "DejaVuSans-Bold.ttf"
        if bold
        else "DejaVuSans.ttf"
    )

    return ImageFont.truetype(
        str(FONT_DIR / filename),
        size
    )


def safe_filename(value):
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def draw_centered_text(draw, text, y, font, fill=WHITE):
    box = draw.textbbox((0, 0), text, font=font)
    text_width = box[2] - box[0]

    draw.text(
        ((WIDTH - text_width) // 2, y),
        text,
        font=font,
        fill=fill
    )


def draw_arrow(draw, start, end, color=ACCENT, width=8):
    draw.line(
        [start, end],
        fill=color,
        width=width
    )

    angle = math.atan2(
        end[1] - start[1],
        end[0] - start[0]
    )

    arrow_length = 25
    arrow_angle = math.pi / 6

    left = (
        end[0] - arrow_length * math.cos(angle - arrow_angle),
        end[1] - arrow_length * math.sin(angle - arrow_angle)
    )

    right = (
        end[0] - arrow_length * math.cos(angle + arrow_angle),
        end[1] - arrow_length * math.sin(angle + arrow_angle)
    )

    draw.polygon(
        [end, left, right],
        fill=color
    )


def draw_card(
    draw,
    x,
    y,
    width,
    height,
    title,
    description="",
    accent=ACCENT
):
    draw.rounded_rectangle(
        (x, y, x + width, y + height),
        radius=24,
        fill=PANEL,
        outline=accent,
        width=4
    )

    title_font = load_font(34, bold=True)

    draw.text(
        (x + 30, y + 30),
        title,
        font=title_font,
        fill=WHITE
    )

    if description:
        description_font = load_font(23)

        draw.text(
            (x + 30, y + 95),
            description,
            font=description_font,
            fill=MUTED
        )


def draw_header(draw, heading):
    draw.text(
        (100, 65),
        heading,
        font=load_font(54, bold=True),
        fill=WHITE
    )

    draw.line(
        (100, 145, WIDTH - 100, 145),
        fill=ACCENT,
        width=4
    )


def draw_footer(draw, text):
    draw.text(
        (100, HEIGHT - 90),
        text,
        font=load_font(22),
        fill=MUTED
    )


def render_architecture(image, draw, heading):
    draw_header(draw, heading)

    card_width = 390
    card_height = 180

    y = 390

    positions = [
        160,
        765,
        1370
    ]

    components = [
        ("Docker CLI", "User commands"),
        ("Docker Engine", "Manages containers"),
        ("Container", "Runs applications")
    ]

    for index, (title, description) in enumerate(components):
        draw_card(
            draw,
            positions[index],
            y,
            card_width,
            card_height,
            title,
            description,
            ACCENT if index != 2 else GREEN
        )

    draw_arrow(
        draw,
        (positions[0] + card_width + 20, y + 90),
        (positions[1] - 20, y + 90)
    )

    draw_arrow(
        draw,
        (positions[1] + card_width + 20, y + 90),
        (positions[2] - 20, y + 90)
    )

    draw_centered_text(
        draw,
        "How Docker components communicate",
        250,
        load_font(32),
        MUTED
    )


def render_image_layers(image, draw, heading):
    draw_header(draw, heading)

    layers = [
        ("Application code", GREEN),
        ("Runtime and dependencies", ACCENT),
        ("Base image", ORANGE)
    ]

    x = 570
    y = 330

    for index, (label, color) in enumerate(layers):
        layer_y = y + index * 145

        draw.rounded_rectangle(
            (x, layer_y, x + 780, layer_y + 105),
            radius=18,
            fill=PANEL,
            outline=color,
            width=5
        )

        draw_centered_text(
            draw,
            label,
            layer_y + 28,
            load_font(30, bold=True),
            WHITE
        )

    draw_centered_text(
        draw,
        "Docker images are built from reusable layers",
        820,
        load_font(30),
        MUTED
    )


def render_container_demo(image, draw, heading):
    draw_header(draw, heading)

    draw_card(
        draw,
        160,
        330,
        700,
        420,
        "Docker Image",
        "node:20-alpine",
        ACCENT
    )

    draw_arrow(
        draw,
        (900, 540),
        (1050, 540),
        GREEN,
        12
    )

    draw_card(
        draw,
        1100,
        330,
        650,
        420,
        "Running Container",
        "my-node-app",
        GREEN
    )

    draw_centered_text(
        draw,
        "docker run --name my-node-app node:20-alpine",
        830,
        load_font(27),
        ORANGE
    )


def render_summary(image, draw, heading):
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

    for (title, description), (x, y) in zip(
        cards,
        positions
    ):
        draw_card(
            draw,
            x,
            y,
            700,
            170,
            title,
            description
        )


def render_generic(image, draw, heading, description):
    draw_header(draw, heading)

    draw.rounded_rectangle(
        (200, 300, 1720, 780),
        radius=30,
        fill=PANEL,
        outline=ACCENT,
        width=4
    )

    words = description.split()
    lines = []
    current = []

    for word in words:
        current.append(word)

        if len(current) >= 12:
            lines.append(" ".join(current))
            current = []

    if current:
        lines.append(" ".join(current))

    font = load_font(31)

    for index, line in enumerate(lines[:8]):
        draw.text(
            (280, 380 + index * 55),
            line,
            font=font,
            fill=WHITE
        )


def classify_scene(scene):
    name = scene.get("name", "").lower()
    heading = scene.get("heading", "").lower()

    if name == "call_to_action":
        return "generic"

    if name == "hook":
        return "architecture"

    if "image" in heading or "layer" in heading:
        return "layers"

    if "container" in heading or "running" in heading:
        return "container"

    if "conclusion" in name or "key takeaway" in heading:
        return "summary"

    if name == "introduction":
        return "architecture"

    return "generic"


def render_scene(scene, output_dir):
    image = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        BACKGROUND
    )

    draw = ImageDraw.Draw(image)

    heading = scene.get(
        "heading",
        "Technical Explanation"
    )

    description = scene.get(
        "visual_suggestion",
        ""
    )

    scene_type = classify_scene(scene)

    if scene_type == "architecture":
        render_architecture(
            image,
            draw,
            heading
        )

    elif scene_type == "layers":
        render_image_layers(
            image,
            draw,
            heading
        )

    elif scene_type == "container":
        render_container_demo(
            image,
            draw,
            heading
        )

    elif scene_type == "summary":
        render_summary(
            image,
            draw,
            heading
        )

    else:
        render_generic(
            image,
            draw,
            heading,
            description
        )

    draw_footer(
        draw,
        f"AI CONTENT STUDIO  |  {scene.get('name', '')}"
    )

    filename = (
        f"{scene['scene_number']:02d}_"
        f"{safe_filename(scene['name'])}.png"
    )

    output_path = output_dir / filename

    image.save(output_path)

    print(f"Created: {output_path}")

    return output_path


def generate_visuals(scene_plan_path, output_dir):
    with open(
        scene_plan_path,
        "r",
        encoding="utf-8"
    ) as file:
        scene_plan = json.load(file)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    generated = []

    for scene in scene_plan["scenes"]:
        generated.append(
            render_scene(scene, output_dir)
        )

    print(
        f"\nGenerated {len(generated)} visual scenes."
    )

    return generated


def main():
    parser = argparse.ArgumentParser(
        description="Generate educational video scene visuals."
    )

    parser.add_argument(
        "--scene-plan",
        required=True
    )

    parser.add_argument(
        "--output-dir",
        required=True
    )

    args = parser.parse_args()

    generate_visuals(
        args.scene_plan,
        args.output_dir
    )


if __name__ == "__main__":
    main()
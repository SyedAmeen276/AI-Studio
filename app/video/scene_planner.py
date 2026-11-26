import argparse
import json
from pathlib import Path


SCENE_GAP_SECONDS = 0.35
TITLE_SCREEN_SECONDS = 5.0


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def build_scene_plan(script, manifest):

    manifest_segments = {
        segment["name"]: segment
        for segment in manifest["segments"]
    }

    scenes = []
    current_time = 0.0

    def add_scene(name, heading, narration, visual, practical_example=None):

        nonlocal current_time

        audio_segment = manifest_segments.get(name)

        if audio_segment is None:
            raise ValueError(
                f"Missing audio segment in manifest: {name}"
            )

        duration = audio_segment["quality"]["duration_seconds"]

        scene = {
            "scene_number": len(scenes) + 1,
            "name": name,
            "heading": heading,
            "narration": narration,
            "visual_suggestion": visual,
            "practical_example": practical_example,
            "start_time": round(current_time, 3),
            "end_time": round(current_time + duration, 3),
            "duration": duration,
            "audio_file": audio_segment["file"],
            "title_overlay_duration": (
                TITLE_SCREEN_SECONDS if name == "hook" else 0
            ),
        }

        scenes.append(scene)

        current_time += duration + SCENE_GAP_SECONDS

    # Hook
    hook = script["hook"]

    add_scene(
        name="hook",
        heading="Introduction",
        narration=hook["narration"],
        visual=hook.get("visual_suggestion", ""),
    )

    # Introduction
    introduction = script["introduction"]

    add_scene(
        name="introduction",
        heading="What is Docker?",
        narration=introduction["narration"],
        visual=introduction.get("visual_suggestion", ""),
    )

    # Main sections
    for index, section in enumerate(script.get("sections", []), start=1):

        name = f"section_{index:02d}"

        add_scene(
            name=name,
            heading=section["heading"],
            narration=section["narration"],
            visual=section.get("visual_suggestion", ""),
            practical_example=section.get("practical_example"),
        )

    # Conclusion
    conclusion = script["conclusion"]

    add_scene(
        name="conclusion",
        heading="Key Takeaways",
        narration=conclusion["narration"],
        visual=conclusion.get("visual_suggestion", ""),
    )

    # Call to action
    cta = script.get("call_to_action", "")

    if isinstance(cta, dict):
        cta = cta.get("narration", "")

    add_scene(
        name="call_to_action",
        heading="Thanks for Watching!",
        narration=cta,
        visual="Subscribe, like and comment animation.",
    )

    # Validate audio duration
    planned_duration = scenes[-1]["end_time"]

    actual_duration = manifest["total_duration_seconds"]

    difference = abs(planned_duration - actual_duration)

    if difference > 0.1:
        raise ValueError(
            f"Scene duration mismatch: "
            f"planned={planned_duration}, "
            f"audio={actual_duration}"
        )

    return {
        "title": script["title"],
        "description": script.get("description", ""),
        "resolution": "1920x1080",
        "fps": 30,
        "total_duration_seconds": actual_duration,
        "title_screen_duration_seconds": TITLE_SCREEN_SECONDS,
        "scenes": scenes,
    }


def main():

    parser = argparse.ArgumentParser(
        description="Create a timed video scene plan."
    )

    parser.add_argument("--script", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    script = load_json(args.script)
    manifest = load_json(args.manifest)

    plan = build_scene_plan(script, manifest)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(plan, file, indent=4, ensure_ascii=False)

    print(f"Created {len(plan['scenes'])} scenes.")
    print(f"Duration: {plan['total_duration_seconds']} seconds")
    print(f"Scene plan: {output_path}")


if __name__ == "__main__":
    main()
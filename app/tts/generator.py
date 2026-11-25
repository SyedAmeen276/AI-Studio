import argparse
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import soundfile as sf

from app.tts.config import (
    AUDIO_OUTPUT_DIR,
    DEFAULT_SPEED,
    DEFAULT_VOICE,
)
from app.tts.engine import KokoroEngine


def extract_narration(script):
    """Extract all spoken content from the generated script."""

    narration_parts = []

    def add(text):
        if isinstance(text, str) and text.strip():
            narration_parts.append(text.strip())

    # Hook
    hook = script.get("hook", {})
    if isinstance(hook, dict):
        add(hook.get("narration"))

    # Introduction
    introduction = script.get("introduction", {})
    if isinstance(introduction, dict):
        add(introduction.get("narration"))

    # Sections
    sections = script.get("sections", [])

    for index, section in enumerate(sections, start=1):
        if not isinstance(section, dict):
            continue

        add(section.get("heading"))
        add(section.get("narration"))

        practical_example = section.get("practical_example")
        if practical_example:
            add("Practical example.")
            add(practical_example)

    # Conclusion
    conclusion = script.get("conclusion", {})
    if isinstance(conclusion, dict):
        add(conclusion.get("narration"))

    # Call to action
    cta = script.get("call_to_action")

    if isinstance(cta, dict):
        add(cta.get("narration"))
    else:
        add(cta)

    return "\n\n".join(narration_parts)


def create_slug(title):
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower())
    return slug.strip("-")


def generate_audio(script_path, voice, speed):

    script_path = Path(script_path).resolve()

    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    with script_path.open("r", encoding="utf-8") as file:
        script = json.load(file)

    title = script.get("title", script_path.stem)

    narration = extract_narration(script)

    if not narration:
        raise ValueError("No narration found in script.")

    output_dir = AUDIO_OUTPUT_DIR / create_slug(title)
    output_dir.mkdir(parents=True, exist_ok=True)

    audio_path = output_dir / "narration.wav"
    metadata_path = output_dir / "metadata.json"

    print("\n===================================")
    print("AI Content Studio - Kokoro TTS")
    print("===================================")

    print("Title:", title)
    print("Voice:", voice)
    print("Speed:", speed)
    print("Narration characters:", len(narration))

    engine = KokoroEngine()

    start_time = time.time()

    result = engine.generate(
        text=narration,
        voice=voice,
        speed=speed,
    )

    generation_time = time.time() - start_time

    sf.write(
        audio_path,
        result["audio"],
        result["sample_rate"],
    )

    metadata = {
        "title": title,
        "source_script": str(script_path),
        "voice": voice,
        "speed": speed,
        "sample_rate": result["sample_rate"],
        "audio_duration_seconds": round(result["duration"], 2),
        "generation_time_seconds": round(generation_time, 2),
        "real_time_factor": round(
            generation_time / result["duration"], 3
        ) if result["duration"] else None,
        "narration_characters": len(narration),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "audio_file": str(audio_path),
    }

    with metadata_path.open("w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=4)

    print("\n===================================")
    print("TTS GENERATION COMPLETED")
    print("===================================")

    print("Audio:", audio_path)
    print("Metadata:", metadata_path)
    print("Duration:", result["duration"], "seconds")
    print("Generation time:", round(generation_time, 2), "seconds")
    print("RTF:", metadata["real_time_factor"])


def main():

    parser = argparse.ArgumentParser(
        description="Generate narration from an AI Content Studio script."
    )

    parser.add_argument(
        "--script",
        required=True,
        help="Path to the generated script.json",
    )

    parser.add_argument(
        "--voice",
        default=DEFAULT_VOICE,
        help="Kokoro voice",
    )

    parser.add_argument(
        "--speed",
        type=float,
        default=DEFAULT_SPEED,
        help="Speech speed",
    )

    args = parser.parse_args()

    if not 0.5 <= args.speed <= 2.0:
        parser.error("Speed must be between 0.5 and 2.0.")

    generate_audio(
        script_path=args.script,
        voice=args.voice,
        speed=args.speed,
    )


if __name__ == "__main__":
    main()
import argparse
import json
import time
from datetime import datetime, timezone

import soundfile as sf

from app.tts.config import (
    AUDIO_OUTPUT_DIR,
    DEFAULT_SPEED,
    SUPPORTED_VOICES,
)
from app.tts.engine import KokoroEngine


SAMPLE_TEXT = """
Welcome to AI Content Studio.

Today, we are exploring how Docker works internally.

Docker uses containers to isolate applications.
Understanding images, containers, and namespaces
is essential for modern software developers.

Let's explore these concepts step by step.
"""


def main():

    parser = argparse.ArgumentParser(
        description="Compare Kokoro TTS voices."
    )

    parser.add_argument(
        "--speed",
        type=float,
        default=DEFAULT_SPEED,
    )

    parser.add_argument(
        "--voices",
        nargs="+",
        choices=list(SUPPORTED_VOICES.keys()),
        default=list(SUPPORTED_VOICES.keys()),
    )

    args = parser.parse_args()

    if not 0.5 <= args.speed <= 2.0:
        parser.error("Speed must be between 0.5 and 2.0.")

    output_dir = AUDIO_OUTPUT_DIR / "voice-comparison"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Initializing Kokoro...")
    engine = KokoroEngine()

    results = []

    for voice in args.voices:

        print(f"\nGenerating voice: {voice}")

        start = time.time()

        result = engine.generate(
            text=SAMPLE_TEXT,
            voice=voice,
            speed=args.speed,
        )

        filename = f"{voice}.wav"
        output_path = output_dir / filename

        sf.write(
            output_path,
            result["audio"],
            result["sample_rate"],
        )

        elapsed = time.time() - start

        record = {
            "voice": voice,
            "description": SUPPORTED_VOICES[voice],
            "file": str(output_path),
            "duration_seconds": round(result["duration"], 2),
            "generation_time_seconds": round(elapsed, 2),
            "speed": args.speed,
        }

        results.append(record)

        print("Saved:", output_path)
        print("Duration:", record["duration_seconds"], "seconds")
        print("Generation time:", record["generation_time_seconds"], "seconds")

    report = {
        "sample_text": SAMPLE_TEXT,
        "speed": args.speed,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "voices": results,
    }

    report_path = output_dir / "comparison.json"

    with report_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    print("\nVoice comparison completed.")
    print("Report:", report_path)


if __name__ == "__main__":
    main()
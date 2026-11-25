import argparse
import json
import re
import time
from pathlib import Path

import numpy as np
import soundfile as sf

from app.tts.config import AUDIO_OUTPUT_DIR, DEFAULT_SPEED, DEFAULT_VOICE
from app.tts.engine import KokoroEngine


def slugify(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def extract_segments(script):
    segments = []

    def add(name, text):
        if isinstance(text, str) and text.strip():
            segments.append({
                "name": name,
                "text": text.strip()
            })

    hook = script.get("hook", {})
    add("hook", hook.get("narration") if isinstance(hook, dict) else hook)

    introduction = script.get("introduction", {})
    add(
        "introduction",
        introduction.get("narration")
        if isinstance(introduction, dict)
        else introduction
    )

    for index, section in enumerate(script.get("sections", []), start=1):
        if not isinstance(section, dict):
            continue

        heading = section.get("heading", f"Section {index}")
        narration = section.get("narration", "")

        if narration.strip():
            segments.append({
                "name": f"section_{index:02d}",
                "text": f"{heading}. {narration}"
            })

    conclusion = script.get("conclusion", {})
    add(
        "conclusion",
        conclusion.get("narration")
        if isinstance(conclusion, dict)
        else conclusion
    )

    cta = script.get("call_to_action", "")
    add(
        "call_to_action",
        cta.get("narration") if isinstance(cta, dict) else cta
    )

    return segments


def validate_audio(audio, sample_rate):
    if audio is None or len(audio) == 0:
        raise ValueError("Generated audio is empty.")

    if not np.all(np.isfinite(audio)):
        raise ValueError("Audio contains NaN or infinite values.")

    peak = float(np.max(np.abs(audio)))
    rms = float(np.sqrt(np.mean(np.square(audio))))

    duration = len(audio) / sample_rate

    if duration <= 0:
        raise ValueError("Invalid audio duration.")

    return {
        "duration_seconds": round(duration, 2),
        "peak_amplitude": round(peak, 4),
        "rms_amplitude": round(rms, 4),
        "clipping_detected": peak >= 0.999,
        "sample_rate": sample_rate,
        "valid": True
    }


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--script", required=True)
    parser.add_argument("--voice", default=DEFAULT_VOICE)
    parser.add_argument("--speed", type=float, default=DEFAULT_SPEED)

    args = parser.parse_args()

    script_path = Path(args.script)

    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    with script_path.open("r", encoding="utf-8") as file:
        script = json.load(file)

    title = script.get("title", script_path.stem)
    output_dir = AUDIO_OUTPUT_DIR / slugify(title)
    segments_dir = output_dir / "segments"

    segments_dir.mkdir(parents=True, exist_ok=True)

    segments = extract_segments(script)

    if not segments:
        raise ValueError("No narration segments found in script.")

    print(f"Title: {title}")
    print(f"Voice: {args.voice}")
    print(f"Segments: {len(segments)}")

    engine = KokoroEngine()

    generated_audio = []
    manifest = {
        "title": title,
        "voice": args.voice,
        "speed": args.speed,
        "segments": []
    }

    sample_rate = None
    silence = None

    for index, segment in enumerate(segments, start=1):
        print(f"\nGenerating {segment['name']}...")

        result = engine.generate(
            text=segment["text"],
            voice=args.voice,
            speed=args.speed
        )

        audio = np.asarray(result["audio"], dtype=np.float32)
        sample_rate = result["sample_rate"]

        quality = validate_audio(audio, sample_rate)

        segment_path = segments_dir / f"{segment['name']}.wav"
        sf.write(segment_path, audio, sample_rate)

        generated_audio.append(audio)

        if silence is None:
            silence = np.zeros(int(sample_rate * 0.35), dtype=np.float32)

        manifest["segments"].append({
            "name": segment["name"],
            "file": str(segment_path.relative_to(output_dir)),
            "generation_time_seconds": round(
                result["generation_time"], 2
            ),
            "quality": quality
        })

        print(f"Saved: {segment_path}")
        print(f"Duration: {quality['duration_seconds']} seconds")
        print(f"Clipping: {quality['clipping_detected']}")

        if index < len(segments):
            generated_audio.append(silence)

    final_audio = np.concatenate(generated_audio)

    final_quality = validate_audio(final_audio, sample_rate)

    final_path = output_dir / "narration.wav"
    sf.write(final_path, final_audio, sample_rate)

    manifest["final_audio"] = {
        "file": "narration.wav",
        "quality": final_quality
    }

    manifest["total_duration_seconds"] = final_quality["duration_seconds"]
    manifest["completed_at"] = time.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    manifest_path = output_dir / "manifest.json"

    with manifest_path.open("w", encoding="utf-8") as file:
        json.dump(manifest, file, indent=2)

    print("\n========== COMPLETE ==========")
    print(f"Final audio: {final_path}")
    print(f"Manifest: {manifest_path}")
    print(f"Duration: {final_quality['duration_seconds']} seconds")
    print(f"Segments: {len(segments)}")
    print(f"Clipping detected: {final_quality['clipping_detected']}")


if __name__ == "__main__":
    main()
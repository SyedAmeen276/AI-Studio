import json
import re
from pathlib import Path


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


def split_into_captions(text, max_words=11):
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    captions = []

    for sentence in sentences:
        words = sentence.split()

        for index in range(0, len(words), max_words):
            chunk = " ".join(words[index:index + max_words])

            if chunk:
                captions.append(chunk)

    return captions


def format_timestamp(seconds):
    milliseconds = int(round(seconds * 1000))

    hours = milliseconds // 3600000
    milliseconds %= 3600000

    minutes = milliseconds // 60000
    milliseconds %= 60000

    secs = milliseconds // 1000
    milliseconds %= 1000

    return (
        f"{hours:02}:"
        f"{minutes:02}:"
        f"{secs:02},"
        f"{milliseconds:03}"
    )


def generate_srt(script_path, manifest_path, output_path):
    with open(script_path, encoding="utf-8") as file:
        script = json.load(file)

    with open(manifest_path, encoding="utf-8") as file:
        manifest = json.load(file)

    segments = extract_segments(script)

    manifest_segments = {
        item["name"]: item
        for item in manifest["segments"]
    }

    current_time = 0.0
    caption_index = 1
    subtitle_entries = []

    for segment in segments:
        name = segment["name"]

        if name not in manifest_segments:
            raise ValueError(f"Missing duration for segment: {name}")

        duration = manifest_segments[name]["quality"]["duration_seconds"]

        captions = split_into_captions(segment["text"])

        if not captions:
            current_time += duration + 0.35
            continue

        total_words = sum(len(caption.split()) for caption in captions)

        segment_time = current_time

        for caption in captions:
            word_count = len(caption.split())
            caption_duration = duration * word_count / total_words

            start = segment_time
            end = segment_time + caption_duration

            subtitle_entries.append(
                f"{caption_index}\n"
                f"{format_timestamp(start)} --> "
                f"{format_timestamp(end)}\n"
                f"{caption}\n"
            )

            caption_index += 1
            segment_time = end

        current_time += duration + 0.35

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        "\n".join(subtitle_entries),
        encoding="utf-8"
    )

    print(f"Generated {caption_index - 1} captions.")
    print(f"Subtitle file: {output_path}")

    return output_path
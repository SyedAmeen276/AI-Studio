import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL", "http://localhost:11434"
)

DEFAULT_MODEL = os.getenv(
    "OLLAMA_MODEL", "qwen2.5:3b"
)

OUTPUT_DIR = Path("/workspace/output/scripts")


def create_slug(text: str) -> str:
    """Convert a topic into a filesystem-friendly directory name."""
    slug = text.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def build_prompt(topic: str, duration: int, audience: str) -> str:
    """Create instructions for YouTube script generation."""

    return f"""
You are an expert YouTube scriptwriter and technical educator.

Create a high-quality YouTube video script using these requirements.

TOPIC: {topic}

VIDEO DURATION: Approximately {duration} minutes.

TARGET AUDIENCE: {audience}

CONTENT REQUIREMENTS:
1. Start with a compelling hook.
2. Make the introduction engaging.
3. Explain concepts progressively.
4. Use practical examples wherever appropriate.
5. Keep technical explanations accurate.
6. Avoid fabricated facts, statistics and references.
7. Use natural conversational English suitable for narration.
8. Include suggestions for visuals.
9. Avoid unnecessary repetition.
10. Finish with a meaningful conclusion and CTA.

For technical topics:
- Prefer correct technical terminology.
- Include practical examples.
- Do not invent APIs, commands or technical behaviour.
- Clearly distinguish facts from simplified analogies.

Return ONLY valid JSON.

Use exactly this JSON structure:

{{
  "title": "YouTube video title",
  "description": "Short YouTube description",
  "target_audience": "{audience}",
  "estimated_duration_minutes": {duration},
  "hook": {{
    "narration": "Opening hook",
    "visual_suggestion": "Suggested opening visual"
  }},
  "introduction": {{
    "narration": "Introduction narration",
    "visual_suggestion": "Suggested visual"
  }},
  "sections": [
    {{
      "heading": "Section heading",
      "narration": "Detailed narration",
      "practical_example": "Practical example",
      "visual_suggestion": "Suggested visual"
    }}
  ],
  "conclusion": {{
    "narration": "Conclusion narration",
    "visual_suggestion": "Suggested visual"
  }},
  "call_to_action": "Ask viewers to subscribe, like or comment"
}}
"""


def generate_script(
    topic: str,
    duration: int,
    audience: str,
    model: str
) -> dict:

    prompt = build_prompt(topic, duration, audience)

    print(f"\nModel: {model}")
    print(f"Ollama: {OLLAMA_BASE_URL}")
    print(f"Topic: {topic}")
    print(f"Duration: {duration} minutes")
    print("\nGenerating script. Please wait...\n")

    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.4
            }
        },
        timeout=900
    )

    response.raise_for_status()

    result = response.json()
    generated_text = result.get("response", "").strip()

    if not generated_text:
        raise ValueError("Ollama returned an empty response.")

    try:
        script = json.loads(generated_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Model returned invalid JSON: {exc}"
        ) from exc

    validate_script(script)

    return script


def validate_script(script: dict) -> None:
    """Validate the required script structure."""

    required_fields = [
        "title",
        "description",
        "target_audience",
        "estimated_duration_minutes",
        "hook",
        "introduction",
        "sections",
        "conclusion",
        "call_to_action"
    ]

    for field in required_fields:
        if field not in script:
            raise ValueError(f"Missing required field: {field}")

    if not isinstance(script["sections"], list):
        raise ValueError("'sections' must be a JSON array.")

    if not script["sections"]:
        raise ValueError("Script must contain at least one section.")

    for field in ["hook", "introduction", "conclusion"]:
        if not isinstance(script[field], dict):
            raise ValueError(f"'{field}' must be a JSON object.")

        if not script[field].get("narration"):
            raise ValueError(f"'{field}' narration is missing.")

    for index, section in enumerate(script["sections"]):
        if not isinstance(section, dict):
            raise ValueError(f"Section {index + 1} must be an object.")

        for field in [
            "heading",
            "narration",
            "practical_example",
            "visual_suggestion"
        ]:
            if not section.get(field):
                raise ValueError(
                    f"Section {index + 1} is missing '{field}'."
                )


def save_script(script: dict, topic: str) -> None:
    """Save generated script in JSON and Markdown formats."""

    slug = create_slug(topic)
    output_path = OUTPUT_DIR / slug

    output_path.mkdir(parents=True, exist_ok=True)

    json_file = output_path / "script.json"
    markdown_file = output_path / "script.md"

    script["generated_at"] = datetime.now(
        timezone.utc
    ).isoformat()

    with json_file.open("w", encoding="utf-8") as file:
        json.dump(
            script,
            file,
            indent=2,
            ensure_ascii=False
        )

    markdown = []

    markdown.append(f"# {script['title']}\n")
    markdown.append(f"**Description:** {script['description']}\n")
    markdown.append(
        f"**Duration:** "
        f"{script['estimated_duration_minutes']} minutes\n"
    )
    markdown.append(
        f"**Audience:** {script['target_audience']}\n"
    )

    markdown.append("\n## Hook\n")
    markdown.append(script["hook"]["narration"])
    markdown.append(
        f"\n\n*Visual: {script['hook']['visual_suggestion']}*\n"
    )

    markdown.append("\n## Introduction\n")
    markdown.append(script["introduction"]["narration"])
    markdown.append(
        f"\n\n*Visual: "
        f"{script['introduction']['visual_suggestion']}*\n"
    )

    markdown.append("\n## Main Content\n")

    for index, section in enumerate(script["sections"], start=1):
        markdown.append(f"\n### {index}. {section['heading']}\n")
        markdown.append(section["narration"])
        markdown.append(
            f"\n\n**Practical Example:** "
            f"{section['practical_example']}\n"
        )
        markdown.append(
            f"\n*Visual: {section['visual_suggestion']}*\n"
        )

    markdown.append("\n## Conclusion\n")
    markdown.append(script["conclusion"]["narration"])
    markdown.append(
        f"\n\n*Visual: "
        f"{script['conclusion']['visual_suggestion']}*\n"
    )

    markdown.append("\n## Call to Action\n")
    markdown.append(script["call_to_action"])

    markdown_file.write_text(
        "\n".join(markdown),
        encoding="utf-8"
    )

    print("\nScript generated successfully!")
    print(f"\nJSON:     {json_file}")
    print(f"Markdown: {markdown_file}")


def main():
    parser = argparse.ArgumentParser(
        description="AI Content Studio - YouTube Script Generator"
    )

    parser.add_argument(
        "--topic",
        required=True,
        help="Topic for the YouTube video"
    )

    parser.add_argument(
        "--duration",
        type=int,
        default=5,
        help="Target video duration in minutes (default: 5)"
    )

    parser.add_argument(
        "--audience",
        default="Beginners and intermediate learners",
        help="Target audience"
    )

    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Ollama model name"
    )

    args = parser.parse_args()

    if args.duration < 1 or args.duration > 60:
        parser.error("Duration must be between 1 and 60 minutes.")

    try:
        script = generate_script(
            topic=args.topic,
            duration=args.duration,
            audience=args.audience,
            model=args.model
        )

        save_script(script, args.topic)

    except requests.RequestException as exc:
        print(f"API request failed: {exc}", file=sys.stderr)
        sys.exit(1)

    except (ValueError, KeyError, TypeError) as exc:
        print(f"Generation failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

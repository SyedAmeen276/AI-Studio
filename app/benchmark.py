import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

OLLAMA_URL = "http://ollama:11434"
APP_DIR = Path("/workspace/app")
OUTPUT_DIR = Path("/workspace/output/benchmarks")

DEFAULT_MODELS = [
    "qwen2.5:3b",
    "llama3.2:3b"
]


def load_topics():
    path = APP_DIR / "benchmark_topics.json"

    with path.open(encoding="utf-8") as file:
        return json.load(file)["topics"]


def slugify(value):
    return re.sub(
        r"[^a-zA-Z0-9]+",
        "-",
        value
    ).strip("-").lower()


def get_available_models():
    response = requests.get(
        f"{OLLAMA_URL}/api/tags",
        timeout=30
    )

    response.raise_for_status()

    return {
        item["name"]
        for item in response.json().get("models", [])
    }


def build_prompt(topic):
    concepts = "\n".join(
        f"- {concept}"
        for concept in topic["concepts"]
    )

    return f"""
You are an expert technical educator and YouTube scriptwriter.

Create a complete educational YouTube script.

TOPIC: {topic['title']}

CATEGORY: {topic['category']}

DURATION: Approximately {topic['duration']} minutes.

AUDIENCE: {topic['audience']}

IMPORTANT CONCEPTS TO COVER:
{concepts}

CONTENT REQUIREMENTS:

1. Start with an engaging 15-30 second hook.
2. Introduce the topic clearly.
3. Explain all important concepts progressively.
4. Include practical and technically correct examples.
5. Explain difficult concepts in beginner-friendly language.
6. Avoid invented statistics and unsupported claims.
7. Avoid repeating the same explanation.
8. Use natural conversational English.
9. Make the script suitable for voice narration.
10. Include useful visual suggestions.
11. End with a meaningful conclusion and CTA.

TECHNICAL ACCURACY:

- Do not invent commands, APIs or technical behaviour.
- Do not confuse related technical concepts.
- Explain limitations and assumptions when relevant.
- If uncertain about a technical detail, avoid presenting it as fact.

OUTPUT FORMAT:

Use these sections:

# Title

# Hook

# Introduction

# Section 1
## Explanation
## Practical Example
## Visual Suggestion

# Section 2
## Explanation
## Practical Example
## Visual Suggestion

Continue with additional sections as necessary.

# Conclusion

# Call to Action

Return only the completed script in Markdown.
"""


def benchmark_model(model, topic):
    prompt = build_prompt(topic)

    print(f"\nModel: {model}")
    print(f"Topic: {topic['title']}")

    start = time.perf_counter()

    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 1400
            },
            "keep_alive": 0
        },
        timeout=1200
    )

    response.raise_for_status()

    elapsed = time.perf_counter() - start
    result = response.json()

    output = result.get("response", "").strip()

    if not output:
        raise ValueError("Empty model response")

    generated_tokens = result.get("eval_count", 0)
    eval_duration = result.get("eval_duration", 0)

    tokens_per_second = (
        generated_tokens / (eval_duration / 1e9)
        if eval_duration else 0
    )

    return {
        "model": model,
        "topic_id": topic["id"],
        "topic": topic["title"],
        "generation_time_seconds": round(elapsed, 2),
        "prompt_tokens": result.get("prompt_eval_count", 0),
        "generated_tokens": generated_tokens,
        "tokens_per_second": round(tokens_per_second, 2),
        "output_characters": len(output),
        "output_words": len(output.split()),
        "output": output
    }


def main():
    parser = argparse.ArgumentParser(
        description="AI Content Studio LLM Benchmark"
    )

    parser.add_argument(
        "--models",
        nargs="+",
        default=DEFAULT_MODELS
    )

    parser.add_argument(
        "--topics",
        nargs="+",
        help="Optional topic IDs to benchmark"
    )

    args = parser.parse_args()

    topics = load_topics()

    if args.topics:
        topics = [
            topic for topic in topics
            if topic["id"] in args.topics
        ]

        if not topics:
            parser.error("No matching topic IDs found.")

    available = get_available_models()

    run_id = datetime.now(
        timezone.utc
    ).strftime("%Y%m%d_%H%M%S")

    run_dir = OUTPUT_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    run_summary = {
        "version": "v0.3",
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "models_requested": args.models,
        "topics": [topic["id"] for topic in topics],
        "results": []
    }

    for model in args.models:
        if model not in available:
            print(f"\nSkipping unavailable model: {model}")

            run_summary["results"].append({
                "model": model,
                "error": "Model not downloaded"
            })

            continue

        for topic in topics:
            model_dir = run_dir / slugify(model)
            model_dir.mkdir(parents=True, exist_ok=True)

            try:
                result = benchmark_model(model, topic)

                script_path = (
                    model_dir / f"{topic['id']}.md"
                )

                script_path.write_text(
                    result.pop("output"),
                    encoding="utf-8"
                )

                metrics_path = (
                    model_dir / f"{topic['id']}.json"
                )

                metrics_path.write_text(
                    json.dumps(result, indent=2),
                    encoding="utf-8"
                )

                result["script_file"] = str(script_path)

                run_summary["results"].append(result)

                print(
                    f"Completed: {model} | "
                    f"{topic['id']} | "
                    f"{result['generation_time_seconds']} sec | "
                    f"{result['tokens_per_second']} tokens/sec"
                )

            except (
                requests.RequestException,
                ValueError
            ) as exc:

                print(
                    f"Failed: {model} | {topic['id']} | {exc}",
                    file=sys.stderr
                )

                run_summary["results"].append({
                    "model": model,
                    "topic_id": topic["id"],
                    "error": str(exc)
                })

    summary_path = run_dir / "benchmark.json"

    summary_path.write_text(
        json.dumps(run_summary, indent=2),
        encoding="utf-8"
    )

    print("\nBenchmark completed.")
    print(f"Results directory: {run_dir}")
    print(f"Summary: {summary_path}")


if __name__ == "__main__":
    main()

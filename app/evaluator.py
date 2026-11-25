import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

APP_DIR = Path("/workspace/app")
OUTPUT_DIR = Path("/workspace/output/benchmarks")

WEIGHTS = {
    "technical_accuracy": 30,
    "completeness": 15,
    "explanation_quality": 15,
    "practical_examples": 10,
    "narration_quality": 10,
    "engagement": 10,
    "structure": 5,
    "instruction_following": 5
}


def load_topics():
    with (APP_DIR / "benchmark_topics.json").open() as file:
        return json.load(file)["topics"]


def find_latest_run():
    runs = sorted(
        [
            path for path in OUTPUT_DIR.iterdir()
            if path.is_dir()
        ],
        reverse=True
    )

    if not runs:
        raise FileNotFoundError("No benchmark runs found.")

    return runs[0]


def normalize(text):
    return re.sub(
        r"\s+",
        " ",
        text.lower()
    ).strip()


def evaluate_script(script_path, topic):
    text = script_path.read_text(
        encoding="utf-8"
    )

    normalized = normalize(text)

    concepts_found = [
        concept for concept in topic["concepts"]
        if normalize(concept) in normalized
    ]

    concept_coverage = (
        len(concepts_found) / len(topic["concepts"])
        if topic["concepts"] else 0
    )

    required_sections = [
        "hook",
        "introduction",
        "conclusion",
        "call to action"
    ]

    sections_found = [
        section for section in required_sections
        if section in normalized
    ]

    section_coverage = (
        len(sections_found) / len(required_sections)
    )

    words = text.split()
    word_count = len(words)

    paragraphs = [
        normalize(paragraph)
        for paragraph in text.split("\n\n")
        if len(paragraph.split()) > 8
    ]

    duplicates = (
        len(paragraphs) - len(set(paragraphs))
    )

    return {
        "word_count": word_count,
        "concepts_found": concepts_found,
        "concepts_missing": [
            concept for concept in topic["concepts"]
            if concept not in concepts_found
        ],
        "concept_coverage_percent": round(
            concept_coverage * 100, 2
        ),
        "sections_found": sections_found,
        "section_coverage_percent": round(
            section_coverage * 100, 2
        ),
        "duplicate_paragraphs": duplicates,
        "automated_checks": {
            "has_hook": "hook" in normalized,
            "has_introduction": "introduction" in normalized,
            "has_conclusion": "conclusion" in normalized,
            "has_cta": "call to action" in normalized,
            "has_minimum_300_words": word_count >= 300
        }
    }


def create_human_scorecard():
    return {
        "instructions": (
            "Review each script manually. Score each category "
            "from 0 to its maximum weight. Do not assume that "
            "concept coverage proves technical correctness."
        ),
        "weights": WEIGHTS,
        "scores": {}
    }


def calculate_human_score(scores):
    total = 0

    for category, maximum in WEIGHTS.items():
        value = scores.get(category)

        if value is None:
            return None

        if not isinstance(value, (int, float)):
            return None

        if value < 0 or value > maximum:
            raise ValueError(
                f"{category} must be between 0 and {maximum}"
            )

        total += value

    return round(total, 2)


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate AI Content Studio benchmark results"
    )

    parser.add_argument(
        "--run",
        help="Benchmark run directory name"
    )

    args = parser.parse_args()

    run_dir = (
        OUTPUT_DIR / args.run
        if args.run
        else find_latest_run()
    )

    summary_path = run_dir / "benchmark.json"

    summary = json.loads(
        summary_path.read_text(encoding="utf-8")
    )

    topics = {
        topic["id"]: topic
        for topic in load_topics()
    }

    evaluation = {
        "run_id": summary["run_id"],
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "results": []
    }

    human_scorecard = create_human_scorecard()

    for result in summary["results"]:
        if result.get("error"):
            continue

        topic_id = result["topic_id"]
        model = result["model"]

        script_path = Path(result["script_file"])

        if not script_path.exists():
            continue

        automated = evaluate_script(
            script_path,
            topics[topic_id]
        )

        evaluation["results"].append({
            "model": model,
            "topic_id": topic_id,
            "generation_time_seconds": result[
                "generation_time_seconds"
            ],
            "tokens_per_second": result[
                "tokens_per_second"
            ],
            "automated_checks": automated
        })

        human_scorecard["scores"].setdefault(
            model, {}
        )[topic_id] = {
            category: None
            for category in WEIGHTS
        }

    evaluation_path = run_dir / "evaluation.json"

    evaluation_path.write_text(
        json.dumps(evaluation, indent=2),
        encoding="utf-8"
    )

    scorecard_path = run_dir / "human_scores.json"

    scorecard_path.write_text(
        json.dumps(human_scorecard, indent=2),
        encoding="utf-8"
    )

    report = [
        "# AI Content Studio v0.3 Benchmark Report",
        "",
        f"Run ID: {summary['run_id']}",
        "",
        "> Automated checks are indicators, not proof of factual accuracy.",
        "",
        "## Results",
        ""
    ]

    report.append(
        "| Model | Topic | Time (sec) | Tokens/sec | "
        "Words | Concept coverage | Missing concepts |"
    )

    report.append(
        "|---|---|---:|---:|---:|---:|---|"
    )

    for item in evaluation["results"]:
        checks = item["automated_checks"]

        report.append(
            f"| {item['model']} "
            f"| {item['topic_id']} "
            f"| {item['generation_time_seconds']} "
            f"| {item['tokens_per_second']} "
            f"| {checks['word_count']} "
            f"| {checks['concept_coverage_percent']}% "
            f"| {', '.join(checks['concepts_missing']) or 'None'} |"
        )

    report.extend([
        "",
        "## Human Evaluation",
        "",
        "Open `human_scores.json` and enter scores for each category.",
        "",
        "| Category | Maximum score |",
        "|---|---:|"
    ])

    for category, weight in WEIGHTS.items():
        report.append(f"| {category} | {weight} |")

    report.extend([
        "",
        "## Important",
        "",
        "- Concept coverage checks literal phrase presence only.",
        "- A model may mention a concept and explain it incorrectly.",
        "- Technical accuracy must be verified against reliable references.",
        "- Review the scripts before selecting a winning model."
    ])

    report_path = run_dir / "comparison.md"

    report_path.write_text(
        "\n".join(report),
        encoding="utf-8"
    )

    print("Evaluation completed.")
    print(f"Evaluation JSON: {evaluation_path}")
    print(f"Human scorecard: {scorecard_path}")
    print(f"Comparison report: {report_path}")


if __name__ == "__main__":
    main()

import argparse
import os
import sys
import requests

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

def generate(prompt: str, model: str) -> str:
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False,
              "options": {"temperature": 0.3}},
        timeout=600,
    )
    response.raise_for_status()
    return response.json().get("response", "").strip()

def main():
    parser = argparse.ArgumentParser(description="AI Content Studio local LLM test")
    parser.add_argument("--prompt", default="Explain Docker in simple terms in 5 bullet points.")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()
    print(f"Model: {args.model}\nOllama: {OLLAMA_BASE_URL}\n\nGenerating...\n")
    try:
        print(generate(args.prompt, args.model))
    except requests.RequestException as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

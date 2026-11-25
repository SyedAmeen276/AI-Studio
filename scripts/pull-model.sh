#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
set -a
[ ! -f .env ] || source .env
set +a
MODEL="${OLLAMA_MODEL:-qwen2.5:3b}"
echo "Pulling ${MODEL}"
docker compose exec ollama ollama pull "${MODEL}"

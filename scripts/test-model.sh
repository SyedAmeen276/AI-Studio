#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PROMPT="${*:-Explain Docker in simple terms in 5 bullet points.}"
docker compose exec -T content-engine python /workspace/app/main.py --prompt "${PROMPT}"

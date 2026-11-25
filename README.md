# AI Content Studio — v0.1

Local-first foundation for an automated YouTube + blog content pipeline.

## Requirements
- macOS with Colima running
- Docker CLI and Docker Compose
- Git

## Start
```bash
cp .env.example .env
chmod +x scripts/*.sh
./scripts/start.sh
```

## Pull the first local model
```bash
./scripts/pull-model.sh
```
Default: `qwen2.5:3b`. Model data is stored in the persistent Docker volume
`ollama_data`, not in Git.

## Test
```bash
./scripts/test-model.sh
./scripts/test-model.sh "Explain C++ unordered_map with a small example."
```

## Operations
```bash
./scripts/status.sh
./scripts/logs.sh
./scripts/stop.sh
```

`docker compose down` removes containers/network but preserves named volumes.
Avoid `docker compose down -v` unless you intend to delete downloaded models.

## Architecture
- `ollama`: local LLM server.
- `content-engine`: Ubuntu 24.04 + Python container.
- `ollama_data`: persistent model storage.
- `app/`: Python source, bind-mounted into the container.
- `output/`: generated files, excluded from Git.

The Python service calls Ollama at `http://ollama:11434` over the private
Compose network. The host port is bound to localhost only.

## v0.1 acceptance criteria
- [ ] Both containers start.
- [ ] Model downloads successfully.
- [ ] Python calls Ollama successfully.
- [ ] Project is committed to local Git.
# AI-Studio
# AI-Studio

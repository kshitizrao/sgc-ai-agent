# SGC AI Agent — Smart Garage Customer AI Agent

Backend-independent AI agent platform for Smart Garage customers. Hybrid Python core + TypeScript SDK.

## Quick Start

```bash
# Start infrastructure
docker compose -f infra/docker-compose.yml up -d

# Install dependencies
uv sync

# Run migrations
uv run --package sgc-db alembic -c packages/db/alembic.ini upgrade head

# Seed sample data
uv run python scripts/seed_db.py

# Start API
uv run --package sgc-agent-api uvicorn agent_api.main:app --reload --app-dir apps/agent-api/src
```

## Architecture

- **apps/agent-api** — FastAPI service (HTTP + WebSocket)
- **packages/agent-core** — LangGraph orchestration
- **packages/tools** — Domain tool registry
- **packages/governance** — AI governance layer
- **packages/llm-providers** — Multi-model LiteLLM router
- **packages/db** — PostgreSQL models & migrations
- **packages/domain-services** — Deterministic business logic
- **sdks/typescript** — `@sgc/agent-sdk` for backend integration

See [docs/architecture.md](docs/architecture.md) for details.

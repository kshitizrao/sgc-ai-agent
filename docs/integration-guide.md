# Integration Guide

## 1. Deploy Agent Service

```bash
docker compose -f infra/docker-compose.yml up -d
uv sync
uv run alembic -c packages/db/alembic.ini upgrade head
uv run python scripts/seed_db.py
```

## 2. Install SDK in Your Backend

```bash
npm install @sgc/agent-sdk
```

## 3. Create Session & Chat

```typescript
import { SgcAgentClient } from "@sgc/agent-sdk";

const agent = new SgcAgentClient({
  baseUrl: process.env.SGC_AGENT_URL!,
  apiKey: process.env.SGC_AGENT_API_KEY!,
});
```

## 4. Optional Webhooks

Register webhook URL for emergency/review events. See `contracts/events/webhook-payload.schema.json`.

## 5. Data Sync

Import parts/services from your backend via CSV:

```bash
uv run python scripts/import_parts_csv.py data/parts.csv
```

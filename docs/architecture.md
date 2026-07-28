# SGC AI Agent Architecture

## Overview

Backend-independent Smart Garage customer AI agent with:
- **Python agent core** (LangGraph-style orchestration, tools, governance)
- **FastAPI service** (HTTP + WebSocket)
- **TypeScript SDK** (`@sgc/agent-sdk`)
- **Agent-owned PostgreSQL** (catalog, operations, marketplace, diagnostics)

## Integration

Your backend passes a **context envelope** only. The agent never reads your DB.

```typescript
const agent = new SgcAgentClient({ baseUrl, apiKey });
const { sessionId } = await agent.createSession({ customerId, context });
const reply = await agent.chat({ sessionId, message, context });
```

## Anti-Hallucination

1. Tool-first: facts from DB via tools
2. Deterministic calculators for pricing, claims, garage scoring
3. Governance fact-check on output amounts
4. Fallback when tools return empty

## Multi-Model

LiteLLM router with task-based routing (self-hosted Ollama + API models).

## Governance

Input/output guardrails, PII redaction, audit trail, prompt registry.

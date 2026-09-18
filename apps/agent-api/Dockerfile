FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml .
COPY packages/ packages/
COPY apps/agent-api/ apps/agent-api/
COPY scripts/ scripts/

RUN uv sync --package sgc-agent-api --package sgc-mcp-server --package sgc-db

EXPOSE 8000

CMD ["uv", "run", "--package", "sgc-agent-api", "uvicorn", "agent_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "apps/agent-api/src"]

"""Structured logging configuration for the SGC AI Agent.

Provides JSON-formatted logs with consistent fields across all components.
Every log entry includes: timestamp, level, component, and optional session_id.

Usage::

    from sgc_shared.logging import setup_logging
    setup_logging()  # Call once at application startup

    import logging
    logger = logging.getLogger("agent.mcp")
    logger.info("Tool called", extra={"tool": "lookup_customer", "duration_ms": 42})

Log categories:
    - agent.intent     : Intent classification decisions
    - agent.mcp        : MCP tool calls and results
    - agent.mcp.server : MCP server-side operations
    - agent.mcp.client : MCP client-side operations
    - agent.mcp.db     : MCP database operations
    - agent.mcp.sql_guard : SQL safety validation
    - agent.llm        : LLM prompt/response pairs
    - agent.orchestrator : Orchestrator flow decisions
    - agent.tool_executor : Tool execution
    - agent.session    : Session lifecycle events
    - agent.db         : Database operations
    - agent.api        : API request/response
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from sgc_shared.config import get_settings


class JSONFormatter(logging.Formatter):
    """Format log records as single-line JSON objects.

    Each log line includes:
    - timestamp (ISO 8601 UTC)
    - level
    - component (logger name)
    - message
    - Any extra fields passed via ``extra={}``
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "component": record.name,
            "message": record.getMessage(),
        }

        # Merge extra fields (skip internal Python logging fields)
        skip = {
            "name", "msg", "args", "created", "relativeCreated",
            "exc_info", "exc_text", "stack_info", "lineno", "funcName",
            "filename", "module", "levelno", "levelname", "pathname",
            "thread", "threadName", "processName", "process",
            "message", "msecs", "taskName",
        }
        for key, value in record.__dict__.items():
            if key not in skip and not key.startswith("_"):
                try:
                    json.dumps(value)  # ensure serialisable
                    log_entry[key] = value
                except (TypeError, ValueError):
                    log_entry[key] = str(value)

        # Include exception info if present
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


class ConsoleFormatter(logging.Formatter):
    """Human-readable coloured console formatter for development."""

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[1;31m",# Bold Red
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        ts = datetime.fromtimestamp(record.created).strftime("%H:%M:%S.%f")[:-3]

        # Collect extra fields
        extra_parts = []
        skip = {
            "name", "msg", "args", "created", "relativeCreated",
            "exc_info", "exc_text", "stack_info", "lineno", "funcName",
            "filename", "module", "levelno", "levelname", "pathname",
            "thread", "threadName", "processName", "process",
            "message", "msecs", "taskName",
        }
        for key, value in record.__dict__.items():
            if key not in skip and not key.startswith("_"):
                extra_parts.append(f"{key}={value}")

        extra_str = f" | {', '.join(extra_parts)}" if extra_parts else ""

        base = (
            f"{color}{ts} | {record.levelname:<5}{self.RESET} | "
            f"{record.name:<30} | {record.getMessage()}{extra_str}"
        )

        if record.exc_info and record.exc_info[1]:
            base += f"\n{self.formatException(record.exc_info)}"

        return base


def setup_logging(
    level: str | None = None,
    log_format: str | None = None,
) -> None:
    """Configure structured logging for the entire application.

    Parameters
    ----------
    level:
        Log level string (DEBUG/INFO/WARNING/ERROR). Falls back to
        ``SG_AI_LOG_LEVEL`` env var, then ``INFO``.
    log_format:
        Format: 'json' or 'text'. Falls back to ``SG_AI_LOG_FORMAT`` env var,
        then 'text' for development.
    """
    settings = get_settings()
    resolved_level = (level or settings.log_level).upper()
    resolved_format = log_format or settings.log_format

    # Remove existing handlers
    root = logging.getLogger()
    root.handlers.clear()

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, resolved_level, logging.INFO))

    if resolved_format == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(ConsoleFormatter())

    root.addHandler(handler)
    root.setLevel(getattr(logging, resolved_level, logging.INFO))

    # Suppress noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    logger = logging.getLogger("agent")
    logger.info(
        "Logging configured",
        extra={"level": resolved_level, "format": resolved_format},
    )

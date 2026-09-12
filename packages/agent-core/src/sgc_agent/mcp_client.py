"""MCP client for connecting to the SGC MCP Server over SSE/HTTP.

This client connects to the MCP server running on a configurable host:port,
discovers available tools, and invokes them on behalf of the agent orchestrator.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from mcp import ClientSession
from mcp.client.sse import sse_client

from sgc_shared.config import get_settings

logger = logging.getLogger("agent.mcp.client")


class MCPClient:
    """Async MCP client that communicates with the SGC MCP Server via SSE.

    Usage::

        client = MCPClient()
        await client.connect()
        result = await client.call_tool("lookup_customer", {"phone_number": "9876543210"})
        await client.disconnect()
    """

    def __init__(self, server_url: str | None = None):
        settings = get_settings()
        self._server_url = server_url or settings.mcp_server_url
        self._session: ClientSession | None = None
        self._read_stream = None
        self._write_stream = None
        self._context_manager = None
        self._tools_cache: list[dict] | None = None

    @property
    def is_connected(self) -> bool:
        return self._session is not None

    async def connect(self) -> None:
        """Connect to the MCP server and initialise the session."""
        if self.is_connected:
            logger.debug("MCP client already connected")
            return

        logger.info("Connecting to MCP server at %s", self._server_url)
        start = time.perf_counter()

        try:
            self._context_manager = sse_client(self._server_url)
            streams = await self._context_manager.__aenter__()
            self._read_stream, self._write_stream = streams

            self._session = ClientSession(self._read_stream, self._write_stream)
            await self._session.__aenter__()
            await self._session.initialize()

            elapsed = round((time.perf_counter() - start) * 1000, 2)
            logger.info(
                "MCP client connected and initialised",
                extra={"server_url": self._server_url, "duration_ms": elapsed},
            )
        except Exception as e:
            logger.error("Failed to connect to MCP server: %s", e, exc_info=True)
            self._session = None
            self._context_manager = None
            raise

    async def disconnect(self) -> None:
        """Gracefully disconnect from the MCP server."""
        if self._session:
            try:
                await self._session.__aexit__(None, None, None)
            except Exception:
                pass
            self._session = None
        if self._context_manager:
            try:
                await self._context_manager.__aexit__(None, None, None)
            except Exception:
                pass
            self._context_manager = None
        self._tools_cache = None
        logger.info("MCP client disconnected")

    async def list_tools(self) -> list[dict]:
        """List all tools available on the MCP server.

        Returns a list of dicts with 'name', 'description', and 'inputSchema'.
        Results are cached for the lifetime of the connection.
        """
        if self._tools_cache is not None:
            return self._tools_cache

        if not self.is_connected:
            await self.connect()

        assert self._session is not None
        result = await self._session.list_tools()
        self._tools_cache = [
            {
                "name": tool.name,
                "description": tool.description or "",
                "inputSchema": tool.inputSchema if hasattr(tool, "inputSchema") else {},
            }
            for tool in result.tools
        ]
        logger.info(
            "Discovered %d MCP tools",
            len(self._tools_cache),
            extra={"tools": [t["name"] for t in self._tools_cache]},
        )
        return self._tools_cache

    async def call_tool(self, tool_name: str, arguments: dict[str, Any] | None = None) -> dict:
        """Call an MCP tool and return the result.

        Parameters
        ----------
        tool_name:
            Name of the tool to invoke.
        arguments:
            Tool arguments as a dict.

        Returns
        -------
        dict
            With keys: 'tool_name', 'success', 'data', 'error'
        """
        if not self.is_connected:
            await self.connect()

        assert self._session is not None
        args = arguments or {}

        logger.info(
            "Calling MCP tool",
            extra={"tool": tool_name, "args": args},
        )
        start = time.perf_counter()

        try:
            result = await self._session.call_tool(tool_name, args)
            elapsed = round((time.perf_counter() - start) * 1000, 2)

            # Extract text content from the result
            data = None
            if result.content:
                text_parts = [c.text for c in result.content if hasattr(c, "text")]
                combined = "\n".join(text_parts)
                try:
                    data = json.loads(combined)
                except json.JSONDecodeError:
                    data = combined

            logger.info(
                "MCP tool call completed",
                extra={
                    "tool": tool_name,
                    "duration_ms": elapsed,
                    "success": not result.isError if hasattr(result, "isError") else True,
                },
            )

            return {
                "tool_name": tool_name,
                "success": not (result.isError if hasattr(result, "isError") else False),
                "data": data,
                "error": None,
            }

        except Exception as e:
            elapsed = round((time.perf_counter() - start) * 1000, 2)
            logger.error(
                "MCP tool call failed",
                extra={"tool": tool_name, "error": str(e), "duration_ms": elapsed},
                exc_info=True,
            )
            return {
                "tool_name": tool_name,
                "success": False,
                "data": None,
                "error": str(e),
            }

    def get_tools_description(self) -> str:
        """Return a formatted description of all tools for use in LLM prompts."""
        if not self._tools_cache:
            return "No tools available. Call list_tools() first."

        lines = []
        for tool in self._tools_cache:
            props = tool.get("inputSchema", {}).get("properties", {})
            params = ", ".join(
                f"{k}: {v.get('type', 'any')} — {v.get('description', '')}"
                for k, v in props.items()
            )
            lines.append(f"- **{tool['name']}**({params}): {tool['description']}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Module-level singleton for shared use
# ---------------------------------------------------------------------------
_client: MCPClient | None = None


async def get_mcp_client() -> MCPClient:
    """Get or create the singleton MCP client."""
    global _client
    if _client is None:
        _client = MCPClient()
    if not _client.is_connected:
        await _client.connect()
        await _client.list_tools()  # Cache tools on first connect
    return _client


async def shutdown_mcp_client() -> None:
    """Shutdown the singleton MCP client."""
    global _client
    if _client is not None:
        await _client.disconnect()
        _client = None

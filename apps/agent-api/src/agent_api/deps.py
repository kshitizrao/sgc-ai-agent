"""FastAPI dependency injection for database sessions.

Provides two database session dependencies:
- ``get_agent_db_session``: Read-write session for sgc_agent (sessions, chats, logs)
- ``get_pikpart_db_session``: Read-only session for prod_pikpart (via MCP)
"""

from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sgc_db.session_dual import get_agent_session, get_pikpart_session


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Default DB session — routes to sgc_agent (read-write).

    This is the primary dependency used by chat, session, and logging endpoints.
    """
    async for session in get_agent_session():
        yield session


async def get_agent_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Explicit sgc_agent session (read-write)."""
    async for session in get_agent_session():
        yield session


async def get_pikpart_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Read-only session for prod_pikpart.

    Used by tools that directly query prod_pikpart outside of MCP.
    """
    async for session in get_pikpart_session():
        yield session

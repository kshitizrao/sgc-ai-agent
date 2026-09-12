"""Dual-database session manager.

Provides separate connection pools for:
- **prod_pikpart** (READ-ONLY): used by the MCP server for data queries
- **sgc_agent** (READ-WRITE): used by the agent for sessions, chats, logs

Both databases are on the same RDS instance but have different credentials
and access patterns.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from sgc_shared.config import get_settings

logger = logging.getLogger("agent.db")

# ── Singletons ─────────────────────────────────────────────────────────
_pikpart_engine: AsyncEngine | None = None
_pikpart_factory: async_sessionmaker[AsyncSession] | None = None

_agent_engine: AsyncEngine | None = None
_agent_factory: async_sessionmaker[AsyncSession] | None = None


# ═══════════════════════════════════════════════════════════════════════════
# prod_pikpart (READ-ONLY)
# ═══════════════════════════════════════════════════════════════════════════

def get_pikpart_engine() -> AsyncEngine:
    global _pikpart_engine
    if _pikpart_engine is None:
        settings = get_settings()
        _pikpart_engine = create_async_engine(
            settings.database_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            execution_options={"postgresql_readonly": True},
        )
        logger.info("Created read-only engine for prod_pikpart")
    return _pikpart_engine


def get_pikpart_session_factory() -> async_sessionmaker[AsyncSession]:
    global _pikpart_factory
    if _pikpart_factory is None:
        _pikpart_factory = async_sessionmaker(
            get_pikpart_engine(), expire_on_commit=False
        )
    return _pikpart_factory


async def get_pikpart_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a read-only async session for prod_pikpart."""
    factory = get_pikpart_session_factory()
    async with factory() as session:
        yield session


# ═══════════════════════════════════════════════════════════════════════════
# sgc_agent (READ-WRITE)
# ═══════════════════════════════════════════════════════════════════════════

def get_agent_engine() -> AsyncEngine:
    global _agent_engine
    if _agent_engine is None:
        settings = get_settings()
        _agent_engine = create_async_engine(
            settings.agent_database_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
        logger.info("Created read-write engine for sgc_agent")
    return _agent_engine


def get_agent_session_factory() -> async_sessionmaker[AsyncSession]:
    global _agent_factory
    if _agent_factory is None:
        _agent_factory = async_sessionmaker(
            get_agent_engine(), expire_on_commit=False
        )
    return _agent_factory


async def get_agent_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a read-write async session for sgc_agent."""
    factory = get_agent_session_factory()
    async with factory() as session:
        yield session


# ═══════════════════════════════════════════════════════════════════════════
# Lifecycle
# ═══════════════════════════════════════════════════════════════════════════

async def dispose_all_engines() -> None:
    """Gracefully close all connection pools."""
    global _pikpart_engine, _pikpart_factory, _agent_engine, _agent_factory

    if _pikpart_engine:
        await _pikpart_engine.dispose()
        logger.info("Disposed prod_pikpart engine")
        _pikpart_engine = None
        _pikpart_factory = None

    if _agent_engine:
        await _agent_engine.dispose()
        logger.info("Disposed sgc_agent engine")
        _agent_engine = None
        _agent_factory = None

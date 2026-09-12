"""Database connection manager for prod_pikpart (READ-ONLY).

This module provides a strictly read-only connection pool to the prod_pikpart
database.  Every session acquired from this pool is unsuitable for writes—
SQLAlchemy's ``execution_options`` flag ``postgresql_readonly`` is set, and the
SQL guard layer validates all queries before execution.
"""

import logging
from collections.abc import AsyncGenerator

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from sgc_shared.config import get_settings

logger = logging.getLogger("agent.mcp.db")

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _get_pikpart_engine() -> AsyncEngine:
    """Create or return the singleton read-only engine for prod_pikpart."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            # Enforce read-only at the connection level
            execution_options={"postgresql_readonly": True},
        )
        logger.info(
            "Created read-only engine for prod_pikpart",
            extra={"pool_size": 5, "max_overflow": 10},
        )
    return _engine


def get_pikpart_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return a session factory bound to the read-only prod_pikpart engine."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            _get_pikpart_engine(),
            expire_on_commit=False,
        )
    return _session_factory


async def get_pikpart_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a read-only async session for prod_pikpart.

    Usage::

        async for session in get_pikpart_session():
            result = await session.execute(text("SELECT ..."))
    """
    factory = get_pikpart_session_factory()
    async with factory() as session:
        yield session


async def dispose_pikpart_engine() -> None:
    """Gracefully close all connections in the pool."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        logger.info("Disposed prod_pikpart engine")
        _engine = None
        _session_factory = None

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from sgc_db.session import get_session


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_session():
        yield session

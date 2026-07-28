from collections.abc import AsyncGenerator

from fastapi import Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from sgc_db.session import get_session
from sgc_shared.config import get_settings


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_session():
        yield session


async def verify_api_key(x_api_key: str = Header(default="")) -> str:
    settings = get_settings()
    if x_api_key != settings.agent_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

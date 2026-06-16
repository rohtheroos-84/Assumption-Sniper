from __future__ import annotations

import asyncio
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

# create async engine with a small pool
engine: AsyncEngine = create_async_engine(
    str(settings.database_url),
    echo=False,
    pool_pre_ping=True,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def check_db() -> bool:
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


# redis lazy client import to avoid startup cost
_redis_client = None


def get_redis():
    global _redis_client
    if _redis_client is None:
        import redis.asyncio as redis

        _redis_client = redis.from_url(str(settings.redis_url), decode_responses=True)
    return _redis_client


async def close_redis() -> None:
    r = get_redis()
    try:
        await r.close()
    except Exception:
        pass

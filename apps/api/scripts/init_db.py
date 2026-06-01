from __future__ import annotations

import asyncio

from app.db import engine
from app.models import Base


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("created tables")


if __name__ == "__main__":
    asyncio.run(init_db())

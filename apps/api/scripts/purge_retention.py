"""Purge expired data according to retention policy."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/assumption_sniper")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
os.environ.setdefault("JWT_SECRET", "purge-secret")

from app.crud.retention import purge_retention_data
from app.db import AsyncSessionLocal


async def main() -> None:
    async with AsyncSessionLocal() as session:
        summary = await purge_retention_data(session)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

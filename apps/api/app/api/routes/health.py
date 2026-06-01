from __future__ import annotations

from fastapi import APIRouter, Depends
from app.core.config import get_settings
from app.db import check_db, get_redis

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/ready")
async def ready() -> dict:
    db_ok = await check_db()
    r = get_redis()
    try:
        redis_ok = await r.ping()
    except Exception:
        redis_ok = False
    overall = db_ok and bool(redis_ok)
    return {"ready": overall, "db": db_ok, "redis": bool(redis_ok)}

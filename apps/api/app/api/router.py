from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import ping

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(ping.router, tags=["system"])

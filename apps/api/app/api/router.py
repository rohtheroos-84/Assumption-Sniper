from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import ping, health

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(ping.router, tags=["system"])
api_router.include_router(health.router, tags=["system"])

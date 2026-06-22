from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import ping, health, ai
from app.api.routes import runs
from app.api.routes import auth
from app.api.routes import data

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(ping.router, tags=["system"])
api_router.include_router(health.router, tags=["system"])
api_router.include_router(ai.router, tags=["ai"])
api_router.include_router(runs.router, tags=["runs"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(data.router, tags=["data"])

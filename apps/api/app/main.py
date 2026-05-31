from __future__ import annotations

import logging
import uuid

from fastapi import FastAPI, Request

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, request_id_var

settings = get_settings()
configure_logging(settings)
logger = logging.getLogger(__name__)

app = FastAPI(title="Assumption Sniper API", version="0.1.0")


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    token = request_id_var.set(request_id)
    try:
        response = await call_next(request)
    finally:
        request_id_var.reset(token)
    response.headers["x-request-id"] = request_id
    return response


app.include_router(api_router)

from __future__ import annotations

import logging
import uuid

from fastapi import FastAPI, Request
from starlette.middleware import Middleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, request_id_var, trace_id_var
from app.core.middleware import RequestSizeLimitMiddleware, RateLimitMiddleware
from app.core.observability_middleware import ObservabilityMiddleware
from app.core.tracing import new_trace_id

settings = get_settings()
configure_logging(settings)
logger = logging.getLogger(__name__)

middleware = [
    Middleware(RequestSizeLimitMiddleware, max_body_size=settings.max_request_size_bytes),
    Middleware(ObservabilityMiddleware),
    Middleware(RateLimitMiddleware),
]

app = FastAPI(title="Assumption Sniper API", version="0.1.0", middleware=middleware)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    trace_id = request.headers.get("x-trace-id") or new_trace_id()
    request_token = request_id_var.set(request_id)
    trace_token = trace_id_var.set(trace_id)
    try:
        response = await call_next(request)
    finally:
        request_id_var.reset(request_token)
        trace_id_var.reset(trace_token)
    response.headers["x-request-id"] = request_id
    response.headers["x-trace-id"] = trace_id
    return response


app.include_router(api_router)

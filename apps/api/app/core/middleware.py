from __future__ import annotations

import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from app.core.config import get_settings
from app.db import get_redis


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_body_size: int = 65536):
        super().__init__(app)
        self.max_body_size = max_body_size

    async def dispatch(self, request: Request, call_next: Callable):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.max_body_size:
                    return PlainTextResponse("request entity too large", status_code=413)
            except ValueError:
                pass
        body = await request.body()
        if len(body) > self.max_body_size:
            return PlainTextResponse("request entity too large", status_code=413)

        async def receive() -> dict:
            return {"type": "http.request", "body": body, "more_body": False}

        request._receive = receive  # type: ignore[attr-defined]
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.settings = get_settings()

    async def dispatch(self, request: Request, call_next: Callable):
        # identify user or fallback to ip
        headers = request.headers
        user_id = headers.get("x-user-id")
        client_host = request.client.host if request.client else "unknown"
        identifier = user_id or client_host

        r = get_redis()

        # ip guardrail
        ip_key = f"rate:ip:{client_host}:{int(time.time() // 60)}"
        ip_count = await r.incr(ip_key)
        if ip_count == 1:
            await r.expire(ip_key, 60)
        if ip_count > self.settings.ip_requests_per_minute:
            return PlainTextResponse("too many requests from ip", status_code=429)

        # route-specific limits
        path = request.url.path
        method = request.method.upper()

        # run creation limits
        if method == "POST" and path.startswith("/api/v1/runs"):
            run_key = f"rate:run:{identifier}:{int(time.time() // 3600)}"
            run_count = await r.incr(run_key)
            if run_count == 1:
                await r.expire(run_key, 3600)
            if run_count > self.settings.run_creation_per_hour:
                return PlainTextResponse("run creation rate limit exceeded", status_code=429)

        # read endpoints
        if method == "GET":
            read_key = f"rate:read:{identifier}:{int(time.time() // 60)}"
            read_count = await r.incr(read_key)
            if read_count == 1:
                await r.expire(read_key, 60)
            if read_count > self.settings.read_requests_per_minute:
                return PlainTextResponse("read rate limit exceeded", status_code=429)

        response = await call_next(request)
        return response

from __future__ import annotations

import hashlib
import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.db import get_redis


def resolve_rate_limit_subject(request: Request) -> tuple[str, str]:
    client_host = request.client.host if request.client else "unknown"

    api_key = request.headers.get("x-api-key")
    if api_key:
        digest = hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:16]
        return f"user:apikey:{digest}", client_host

    authorization = request.headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
        try:
            payload = decode_access_token(token)
            subject = payload.get("sub")
            if subject:
                return f"user:{subject}", client_host
        except Exception:
            pass

    return f"ip:{client_host}", client_host


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
        user_subject, client_host = resolve_rate_limit_subject(request)
        r = get_redis()

        ip_key = f"rate:ip:{client_host}:{int(time.time() // 60)}"
        ip_count = await r.incr(ip_key)
        if ip_count == 1:
            await r.expire(ip_key, 60)
        if ip_count > self.settings.ip_requests_per_minute:
            return PlainTextResponse("too many requests from ip", status_code=429)

        path = request.url.path
        method = request.method.upper()

        if path in {"/api/v1/metrics", "/api/v1/ping", "/api/v1/health", "/api/v1/ready", "/api/v1/demo/sample", "/api/v1/demo/preview", "/api/v1/beta/status"}:
            return await call_next(request)

        if method == "POST" and path.startswith("/api/v1/runs"):
            run_key = f"rate:run:{user_subject}:{int(time.time() // 3600)}"
            run_count = await r.incr(run_key)
            if run_count == 1:
                await r.expire(run_key, 3600)
            if run_count > self.settings.run_creation_per_hour:
                return PlainTextResponse("run creation rate limit exceeded", status_code=429)

            burst_key = f"rate:run_burst:{user_subject}:{int(time.time() // 60)}"
            burst_count = await r.incr(burst_key)
            if burst_count == 1:
                await r.expire(burst_key, 60)
            if burst_count > self.settings.run_burst_per_minute:
                return PlainTextResponse("run creation burst limit exceeded", status_code=429)

        if method == "GET":
            read_key = f"rate:read:{user_subject}:{int(time.time() // 60)}"
            read_count = await r.incr(read_key)
            if read_count == 1:
                await r.expire(read_key, 60)
            if read_count > self.settings.read_requests_per_minute:
                return PlainTextResponse("read rate limit exceeded", status_code=429)

        response = await call_next(request)
        return response

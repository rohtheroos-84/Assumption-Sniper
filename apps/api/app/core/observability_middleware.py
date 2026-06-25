from __future__ import annotations

import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import log_structured, trace_id_var
from app.core.metrics import record_http_request


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration = time.perf_counter() - start
            path = request.url.path
            method = request.method.upper()
            record_http_request(method, path, status_code, duration)
            log_structured(
                "http request completed",
                method=method,
                path=path,
                status_code=status_code,
                duration_ms=round(duration * 1000.0, 2),
                trace_id=trace_id_var.get(),
            )

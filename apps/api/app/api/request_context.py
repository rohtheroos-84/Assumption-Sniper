from __future__ import annotations

from fastapi import Request

from app.core.logging import request_id_var


def audit_context(request: Request) -> dict[str, str | None]:
    return {
        "ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "request_id": request_id_var.get(),
    }

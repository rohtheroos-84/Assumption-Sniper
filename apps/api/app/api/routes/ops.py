from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.config import get_settings
from app.core.tracing import load_trace
from app.crud.core import get_run_with_project
from app.db import get_session
from app.models import User

router = APIRouter(prefix="/ops", tags=["ops"])
settings = get_settings()


@router.get("/slo")
async def slo_status() -> dict:
    return {
        "targets": {
            "api_latency_p95_ms": settings.slo_api_latency_p95_ms,
            "error_rate_percent": settings.slo_error_rate_percent,
            "pipeline_success_percent": settings.slo_pipeline_success_percent,
            "budget_usd_per_hour": settings.budget_alert_usd_per_hour,
        },
        "prometheus_rules": "docs/observability/prometheus-alerts.yml",
        "dashboard": "docs/observability/grafana-dashboard.json",
    }


@router.get("/traces/{run_id}")
async def get_run_trace(
    run_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    row = await get_run_with_project(session, run_id)
    if not row:
        raise HTTPException(status_code=404, detail="run not found")
    _run, project = row
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="forbidden")
    trace = await load_trace(run_id)
    if not trace:
        raise HTTPException(status_code=404, detail="trace not found")
    return trace

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_optional_user
from app.core.config import get_settings
from app.crud import launch as launch_crud
from app.db import get_session
from app.models import User

router = APIRouter(tags=["launch"])
settings = get_settings()

DEMO_SAMPLE = {
    "id": "campus-food-delivery",
    "title": "Campus food delivery",
    "input_text": "On-demand hot food delivery to college dorms using gig drivers and a mobile app",
    "preview": {
        "assumptions": [
            {"assumption_text": "Students will pay a premium for faster dorm delivery", "category": "demand"},
            {"assumption_text": "Gig driver supply is stable during peak hours", "category": "operations"},
            {"assumption_text": "Unit economics work at campus density", "category": "finance"},
        ],
        "critiques": [
            {"critique_text": "Driver supply collapses during finals week, breaking SLAs", "severity": 78},
            {"critique_text": "Campus routing costs are underestimated without dedicated ops", "severity": 72},
        ],
        "risk_score": 64,
    },
}


class FeedbackIn(BaseModel):
    message: str = Field(min_length=3, max_length=4000)
    category: str = Field(default="general", max_length=64)
    page: str | None = None
    rating: int | None = Field(default=None, ge=1, le=5)
    session_id: str | None = None


class AnalyticsEventIn(BaseModel):
    session_id: str
    event_name: str = Field(min_length=1, max_length=128)
    page: str | None = None
    payload: dict | None = None


class AnalyticsBatchIn(BaseModel):
    events: list[AnalyticsEventIn] = Field(min_length=1, max_length=50)


@router.get("/demo/sample")
async def demo_sample():
    return DEMO_SAMPLE


@router.post("/demo/preview")
async def demo_preview(payload: dict):
    idea = str(payload.get("input_text") or DEMO_SAMPLE["input_text"]).strip()
    if not idea:
        raise HTTPException(status_code=400, detail="input_text required")
    return {
        "dry_run": True,
        "input_text": idea,
        "stages": ["decomposition", "assumptions", "critique", "simulation", "reconstruction"],
        "preview": DEMO_SAMPLE["preview"],
        "message": "Demo preview uses sample outputs. Sign up for a full run.",
    }


@router.get("/beta/status")
async def beta_status():
    return {
        "beta_enabled": settings.beta_enabled,
        "invite_required": settings.beta_enabled,
        "cohorts": ["founders", "pm"],
    }


@router.post("/feedback")
async def submit_feedback(
    body: FeedbackIn,
    session: AsyncSession = Depends(get_session),
    current_user: User | None = Depends(get_optional_user),
):
    item = await launch_crud.create_feedback(
        session,
        message=body.message,
        category=body.category,
        user_id=current_user.id if current_user else None,
        session_id=body.session_id,
        page=body.page,
        rating=body.rating,
    )
    return {"id": item.id, "status": "received"}


@router.post("/analytics/events")
async def ingest_analytics(
    body: AnalyticsBatchIn,
    session: AsyncSession = Depends(get_session),
    current_user: User | None = Depends(get_optional_user),
):
    user_id = current_user.id if current_user else None
    events = [
        {
            "session_id": event.session_id,
            "user_id": user_id,
            "event_name": event.event_name,
            "page": event.page,
            "payload": event.payload,
        }
        for event in body.events
    ]
    count = await launch_crud.record_analytics_events(session, events)
    return {"recorded": count}


@router.get("/ops/feedback")
async def list_feedback(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    limit: int = Query(default=50, ge=1, le=200),
):
    rows = await launch_crud.list_feedback(session, limit=limit)
    return [
        {
            "id": row.id,
            "category": row.category,
            "message": row.message,
            "page": row.page,
            "rating": row.rating,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]


@router.get("/ops/success-metrics")
async def success_metrics(session: AsyncSession = Depends(get_session)):
    from sqlalchemy import func, select

    from app.models import Feedback, Run, UsageRecord

    run_count = (await session.execute(select(func.count(Run.id)))).scalar() or 0
    feedback_count = (await session.execute(select(func.count(Feedback.id)))).scalar() or 0
    total_cost = (await session.execute(select(func.sum(UsageRecord.cost_usd)))).scalar() or 0
    total_tokens = (await session.execute(select(func.sum(UsageRecord.tokens)))).scalar() or 0

    return {
        "runs_total": int(run_count),
        "feedback_total": int(feedback_count),
        "tokens_total": int(total_tokens or 0),
        "cost_usd_total": float(total_cost or 0),
        "routing_profile": settings.routing_profile,
        "targets": {
            "weekly_active_runs": 50,
            "critique_relevance_min": 0.6,
            "monthly_retention_percent": 40,
        },
    }

from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncGenerator

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.api.request_context import audit_context
from app.crud import audit as audit_crud
from app.core.config import get_settings
from app.core.pagination import clamp_limit, serialize_page
from app.core.queue import QueueTask, complete_pipeline_task, try_enqueue_pipeline
from app.crud.assumptions import list_assumptions_for_project
from app.crud.core import (
    create_project,
    create_run,
    get_run_with_project,
    list_runs_for_user,
    record_run_event,
    update_run_status,
)
from app.crud.critiques import list_critiques_for_project
from app.crud.reconstructions import list_reconstructions_for_project
from app.crud.scores import list_scores_for_project
from app.crud.simulations import list_simulations_for_project
from app.db import AsyncSessionLocal, get_redis, get_session
from app.models import Project, Run, RunEvent
from app.pipeline.orchestrator import orchestrator

router = APIRouter()
settings = get_settings()


class CreateRunRequest(BaseModel):
    title: str = Field(min_length=1)
    input_text: str | None = None


async def _require_run_access(session: AsyncSession, run_id: str, user_id: str) -> tuple[Run, Project]:
    row = await get_run_with_project(session, run_id)
    if not row:
        raise HTTPException(status_code=404, detail="run not found")
    run, project = row
    if project.user_id != user_id:
        raise HTTPException(status_code=403, detail="forbidden")
    return run, project


async def _run_pipeline_task(run_id: str, project_id: str, user_id: str | None) -> None:
    redis = get_redis()
    try:
        await orchestrator.run_pipeline(run_id, project_id)
    finally:
        await complete_pipeline_task(redis, user_id)


@router.post("/runs")
async def create_run_endpoint(
    request: CreateRunRequest,
    http_request: Request,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_active_user),
):
    input_text = request.input_text or request.title
    project = await create_project(session, current_user.id, request.title, input_text)
    run = await create_run(session, project.id)
    ctx = audit_context(http_request)
    await audit_crud.record_audit(
        session,
        actor_id=current_user.id,
        action="run.create",
        resource_type="run",
        resource_id=run.id,
        meta={"project_id": project.id},
        **ctx,
    )
    return {
        "id": run.id,
        "run_id": run.id,
        "project_id": project.id,
        "status": run.status,
        "title": project.title,
    }


@router.get("/runs")
async def list_runs(
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_active_user),
    limit: int | None = Query(default=None),
    cursor: str | None = Query(default=None),
):
    page_limit = clamp_limit(limit, default=settings.default_page_size, maximum=settings.max_page_size)
    page = await list_runs_for_user(session, current_user.id, limit=page_limit, cursor=cursor)
    return serialize_page(
        page.items,
        page,
        lambda run: {
            "id": run.id,
            "project_id": run.project_id,
            "status": run.status,
            "started_at": run.started_at,
            "finished_at": run.finished_at,
        },
    )


@router.get("/runs/{run_id}")
async def get_run(
    run_id: str,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_active_user),
):
    run, project = await _require_run_access(session, run_id, current_user.id)
    return {
        "id": run.id,
        "project_id": run.project_id,
        "status": run.status,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
        "model_profile": run.model_profile,
        "cost_usd": run.cost_usd,
        "token_total": run.token_total,
        "project": {
            "id": project.id,
            "title": project.title,
            "input_text": project.input_text,
        },
        "input_text": project.input_text,
        "title": project.title,
    }


@router.get("/runs/{run_id}/assumptions")
async def list_run_assumptions(
    run_id: str,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_active_user),
    limit: int | None = Query(default=None),
    cursor: str | None = Query(default=None),
):
    run, _project = await _require_run_access(session, run_id, current_user.id)
    page_limit = clamp_limit(limit, default=settings.default_page_size, maximum=settings.max_page_size)
    page = await list_assumptions_for_project(session, run.project_id, limit=page_limit, cursor=cursor)
    return serialize_page(
        page.items,
        page,
        lambda item: {
            "id": item.id,
            "assumption_text": item.assumption_text,
            "category": item.category,
            "confidence_score": item.confidence_score,
        },
    )


@router.get("/runs/{run_id}/critiques")
async def list_run_critiques(
    run_id: str,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_active_user),
    limit: int | None = Query(default=None),
    cursor: str | None = Query(default=None),
):
    run, _project = await _require_run_access(session, run_id, current_user.id)
    page_limit = clamp_limit(limit, default=settings.default_page_size, maximum=settings.max_page_size)
    page = await list_critiques_for_project(session, run.project_id, limit=page_limit, cursor=cursor)
    return serialize_page(
        page.items,
        page,
        lambda item: {
            "id": item.id,
            "assumption_id": item.assumption_id,
            "text": item.critique_text,
            "summary": item.critique_text,
            "severity": item.severity,
        },
    )


@router.get("/runs/{run_id}/simulations")
async def list_run_simulations(
    run_id: str,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_active_user),
    limit: int | None = Query(default=None),
    cursor: str | None = Query(default=None),
):
    run, _project = await _require_run_access(session, run_id, current_user.id)
    page_limit = clamp_limit(limit, default=settings.default_page_size, maximum=settings.max_page_size)
    page = await list_simulations_for_project(session, run.project_id, limit=page_limit, cursor=cursor)
    return serialize_page(
        page.items,
        page,
        lambda item: {
            "id": item.id,
            "scenario": item.scenario,
            "likelihood": item.likelihood,
            "impact": item.impact,
            "affected_assumptions": item.affected_assumptions_json or [],
        },
    )


@router.get("/runs/{run_id}/reconstructions")
async def list_run_reconstructions(
    run_id: str,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_active_user),
    limit: int | None = Query(default=None),
    cursor: str | None = Query(default=None),
):
    run, _project = await _require_run_access(session, run_id, current_user.id)
    page_limit = clamp_limit(limit, default=settings.default_page_size, maximum=settings.max_page_size)
    page = await list_reconstructions_for_project(session, run.project_id, limit=page_limit, cursor=cursor)
    return serialize_page(
        page.items,
        page,
        lambda item: {
            "id": item.id,
            "rebuilt_idea": item.rebuilt_idea,
            "key_changes": item.key_changes_json or [],
            "risk_reductions": item.risk_reductions_json or [],
        },
    )


@router.get("/runs/{run_id}/scores")
async def list_run_scores(
    run_id: str,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_active_user),
    limit: int | None = Query(default=None),
    cursor: str | None = Query(default=None),
):
    run, _project = await _require_run_access(session, run_id, current_user.id)
    page_limit = clamp_limit(limit, default=settings.default_page_size, maximum=settings.max_page_size)
    page = await list_scores_for_project(session, run.project_id, limit=page_limit, cursor=cursor)
    return serialize_page(
        page.items,
        page,
        lambda item: {
            "id": item.id,
            "assumption_id": item.assumption_id,
            "risk_score": item.risk_score,
            "confidence_score": item.confidence_score,
        },
    )


@router.post("/runs/{run_id}/start")
async def start_run(
    run_id: str,
    background_tasks: BackgroundTasks,
    http_request: Request,
    project_id: str | None = None,
    background: bool = True,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_active_user),
):
    if not run_id or run_id == "new":
        if not project_id:
            raise HTTPException(status_code=400, detail="project_id required")
        project = await session.get(Project, project_id)
        if not project or project.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="forbidden")
        run = await create_run(session, project_id)
        run_id = run.id
    else:
        await _require_run_access(session, run_id, current_user.id)
        if not project_id:
            run = await session.get(Run, run_id)
            if not run:
                raise HTTPException(status_code=404, detail="run not found")
            project_id = run.project_id

    redis = get_redis()
    ok, reason = await try_enqueue_pipeline(
        redis,
        QueueTask(run_id=run_id, project_id=project_id, user_id=current_user.id),
    )
    if not ok:
        raise HTTPException(status_code=429, detail=reason or "queue unavailable")

    ctx = audit_context(http_request)
    await audit_crud.record_audit(
        session,
        actor_id=current_user.id,
        action="run.start",
        resource_type="run",
        resource_id=run_id,
        meta={"project_id": project_id},
        **ctx,
    )

    if background:
        background_tasks.add_task(_run_pipeline_task, run_id, project_id, current_user.id)
        return {"run_id": run_id, "status": "queued"}

    await _run_pipeline_task(run_id, project_id, current_user.id)
    return {"run_id": run_id, "status": "finished"}


@router.post("/runs/{run_id}/cancel")
async def cancel_run(
    run_id: str,
    http_request: Request,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_active_user),
):
    await _require_run_access(session, run_id, current_user.id)
    await update_run_status(session, run_id, "cancelled")
    await record_run_event(session, run_id, stage="orchestration", event_type="cancel_requested", payload_json={})
    ctx = audit_context(http_request)
    await audit_crud.record_audit(
        session,
        actor_id=current_user.id,
        action="run.cancel",
        resource_type="run",
        resource_id=run_id,
        **ctx,
    )
    return {"run_id": run_id, "status": "cancelled"}


@router.post("/runs/{run_id}/retry")
async def retry_run(
    run_id: str,
    background_tasks: BackgroundTasks,
    background: bool = True,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_active_user),
):
    run, _project = await _require_run_access(session, run_id, current_user.id)
    await update_run_status(session, run_id, "queued")
    await record_run_event(session, run_id, stage="orchestration", event_type="retry_requested", payload_json={})

    redis = get_redis()
    ok, reason = await try_enqueue_pipeline(
        redis,
        QueueTask(run_id=run_id, project_id=run.project_id, user_id=current_user.id),
    )
    if not ok:
        raise HTTPException(status_code=429, detail=reason or "queue unavailable")

    if background:
        background_tasks.add_task(_run_pipeline_task, run_id, run.project_id, current_user.id)
        return {"run_id": run_id, "status": "queued"}
    await _run_pipeline_task(run_id, run.project_id, current_user.id)
    return {"run_id": run_id, "status": "finished"}


def _serialize_event(event: RunEvent) -> dict[str, Any]:
    return {
        "id": event.id,
        "stage": event.stage,
        "event_type": event.event_type,
        "payload": event.payload_json or {},
        "created_at": event.created_at.isoformat() if event.created_at else None,
        "message": f"{event.stage}:{event.event_type}",
        "type": event.event_type,
    }


async def _fetch_events_after(session: AsyncSession, run_id: str, last_created_at) -> list[RunEvent]:
    stmt = select(RunEvent).where(RunEvent.run_id == run_id).order_by(RunEvent.created_at.asc())
    if last_created_at is not None:
        stmt = stmt.where(RunEvent.created_at > last_created_at)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def event_stream(run_id: str) -> AsyncGenerator[str, None]:
    last_created_at = None
    terminal_statuses = {"finished", "failed", "cancelled"}

    if settings.sse_use_redis_pubsub:
        redis = get_redis()
        pubsub = redis.pubsub()
        await pubsub.subscribe(f"run_events:{run_id}")
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=settings.sse_poll_interval_seconds)
                if message and message.get("type") == "message":
                    payload = json.loads(message["data"])
                    yield f"data: {json.dumps(payload)}\n\n"
                    if payload.get("event_type") in {"finished", "stage_failed", "cancelled"}:
                        break
                async with AsyncSessionLocal() as session:
                    run = await session.get(Run, run_id)
                    if run and run.status in terminal_statuses:
                        break
                await asyncio.sleep(settings.sse_poll_interval_seconds)
        finally:
            await pubsub.unsubscribe(f"run_events:{run_id}")
            await pubsub.close()
        return

    while True:
        async with AsyncSessionLocal() as session:
            events = await _fetch_events_after(session, run_id, last_created_at)
            run = await session.get(Run, run_id)
            for event in events:
                last_created_at = event.created_at
                yield f"data: {json.dumps(_serialize_event(event))}\n\n"
                if event.event_type in {"finished", "stage_failed", "cancelled"}:
                    return
            if run and run.status in terminal_statuses and not events:
                return
        await asyncio.sleep(settings.sse_poll_interval_seconds)


@router.get("/runs/{run_id}/events")
async def run_events(
    run_id: str,
    session: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_active_user),
):
    await _require_run_access(session, run_id, current_user.id)
    return StreamingResponse(event_stream(run_id), media_type="text/event-stream")

from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal
from app.crud.core import create_run, record_run_event, update_run_status
from app.pipeline.orchestrator import orchestrator
from app.db import get_session
from fastapi import Depends
from app.models import Run, RunEvent, Project

router = APIRouter()


@router.get("/runs/{run_id}")
async def get_run(run_id: str, session: AsyncSession = Depends(get_session)):
    stmt = select(Run, Project).join(Project, Run.project_id == Project.id).where(Run.id == run_id)
    result = await session.execute(stmt)
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="run not found")

    run, project = row
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


@router.post("/runs/{run_id}/start")
async def start_run(run_id: str, project_id: str | None = None, background: bool = True, background_tasks: BackgroundTasks | None = None, session: AsyncSession = Depends(get_session)):
    # if run doesn't exist, create one
    if not run_id or run_id == "new":
        run = await create_run(session, project_id)
        run_id = run.id
    if not project_id:
        project_id = run.project_id

    if background:
        if background_tasks is None:
            raise HTTPException(status_code=400, detail="background tasks not provided")
        background_tasks.add_task(orchestrator.run_pipeline, run_id, project_id, True)
        return {"run_id": run_id, "status": "queued"}

    # synchronous
    await orchestrator.run_pipeline(run_id, project_id, False)
    return {"run_id": run_id, "status": "finished"}


@router.post("/runs/{run_id}/cancel")
async def cancel_run(run_id: str, session: AsyncSession = Depends(get_session)):
    await update_run_status(session, run_id, "cancelled")
    await record_run_event(session, run_id, stage="orchestration", event_type="cancel_requested", payload_json={})
    return {"run_id": run_id, "status": "cancelled"}


@router.post("/runs/{run_id}/retry")
async def retry_run(run_id: str, background: bool = True, background_tasks: BackgroundTasks | None = None, session: AsyncSession = Depends(get_session)):
    # reset status and re-queue
    await update_run_status(session, run_id, "queued")
    await record_run_event(session, run_id, stage="orchestration", event_type="retry_requested", payload_json={})
    # fetch project id
    async with AsyncSessionLocal() as s:
        r = await s.get(Run, run_id)
        project_id = r.project_id if r else None
    if background:
        if background_tasks is None:
            raise HTTPException(status_code=400, detail="background tasks not provided")
        background_tasks.add_task(orchestrator.run_pipeline, run_id, project_id, True)
        return {"run_id": run_id, "status": "queued"}
    await orchestrator.run_pipeline(run_id, project_id, False)
    return {"run_id": run_id, "status": "finished"}


async def event_stream(run_id: str) -> AsyncGenerator[str, None]:
    last_id = None
    while True:
        async with AsyncSessionLocal() as s:
            q = await s.execute("SELECT id, stage, event_type, payload_json, created_at FROM run_events WHERE run_id = :rid AND (:last_id IS NULL OR created_at > (SELECT created_at FROM run_events WHERE id = :last_id)) ORDER BY created_at ASC", {"rid": run_id, "last_id": last_id})
            rows = q.fetchall()
            for row in rows:
                last_id = row[0]
                payload = {"stage": row[1], "event_type": row[2], "payload": row[3], "created_at": str(row[4])}
                yield f"data: {json.dumps(payload)}\n\n"
        await asyncio.sleep(1)


@router.get("/runs/{run_id}/events")
async def run_events(run_id: str):
    return StreamingResponse(event_stream(run_id), media_type="text/event-stream")

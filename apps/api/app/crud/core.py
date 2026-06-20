from __future__ import annotations

from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db import get_redis
from app.models import Project, Run, Assumption, RunEvent

settings = get_settings()


async def create_project(session: AsyncSession, user_id: str, title: Optional[str], input_text: str) -> Project:
    project = Project(user_id=user_id, title=title, input_text=input_text)
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


async def get_project(session: AsyncSession, project_id: str) -> Optional[Project]:
    q = select(Project).where(Project.id == project_id)
    r = await session.execute(q)
    return r.scalar_one_or_none()


async def create_run(session: AsyncSession, project_id: str) -> Run:
    run = Run(project_id=project_id, status="queued")
    session.add(run)
    await session.commit()
    await session.refresh(run)
    return run


async def create_assumption(session: AsyncSession, project_id: str, text: str, category: Optional[str] = None) -> Assumption:
    a = Assumption(project_id=project_id, assumption_text=text, category=category)
    session.add(a)
    await session.commit()
    await session.refresh(a)
    return a


async def record_run_event(session: AsyncSession, run_id: str, stage: str, event_type: str, payload_json: dict) -> RunEvent:
    event = RunEvent(run_id=run_id, stage=stage, event_type=event_type, payload_json=payload_json)
    session.add(event)
    await session.commit()
    await session.refresh(event)
    if settings.sse_use_redis_pubsub:
        redis = get_redis()
        import json

        message = {
            "id": event.id,
            "run_id": run_id,
            "stage": stage,
            "event_type": event_type,
            "payload": payload_json,
            "created_at": event.created_at.isoformat() if event.created_at else None,
        }
        await redis.publish(f"run_events:{run_id}", json.dumps(message))
    return event


async def get_run_with_project(session: AsyncSession, run_id: str) -> tuple[Run, Project] | None:
    stmt = select(Run, Project).join(Project, Run.project_id == Project.id).where(Run.id == run_id)
    result = await session.execute(stmt)
    row = result.first()
    if not row:
        return None
    return row[0], row[1]


async def list_runs_for_user(
    session: AsyncSession,
    user_id: str,
    *,
    limit: int,
    cursor: str | None = None,
):
    from app.core.pagination import paginate_by_id

    stmt = (
        select(Run)
        .join(Project, Run.project_id == Project.id)
        .where(Project.user_id == user_id)
    )
    return await paginate_by_id(session, stmt, id_column=Run.id, limit=limit, cursor=cursor)


async def record_run_usage(
    session: AsyncSession,
    run_id: str,
    *,
    model_profile: Optional[str],
    token_total: int,
    cost_usd: float,
) -> None:
    stmt = (
        update(Run)
        .where(Run.id == run_id)
        .values(model_profile=model_profile, token_total=token_total, cost_usd=cost_usd)
    )
    await session.execute(stmt)
    await session.commit()


async def update_run_status(session: AsyncSession, run_id: str, status: str) -> None:
    stmt = (
        update(Run).where(Run.id == run_id).values(status=status)
    )
    await session.execute(stmt)
    await session.commit()

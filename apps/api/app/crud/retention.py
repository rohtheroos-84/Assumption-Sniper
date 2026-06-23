from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import (
    Assumption,
    AssumptionEdge,
    Critique,
    Decomposition,
    Project,
    Reconstruction,
    Run,
    RunEvent,
    Score,
    Simulation,
    UsageRecord,
    User,
)

settings = get_settings()


async def delete_project_data(session: AsyncSession, project_id: str) -> None:
    run_ids = (
        await session.execute(select(Run.id).where(Run.project_id == project_id))
    ).scalars().all()
    if run_ids:
        await session.execute(delete(RunEvent).where(RunEvent.run_id.in_(run_ids)))
    await session.execute(delete(UsageRecord).where(UsageRecord.project_id == project_id))
    await session.execute(delete(Score).where(Score.project_id == project_id))
    await session.execute(delete(Critique).where(Critique.project_id == project_id))
    await session.execute(delete(Simulation).where(Simulation.project_id == project_id))
    await session.execute(delete(Reconstruction).where(Reconstruction.project_id == project_id))
    await session.execute(delete(Decomposition).where(Decomposition.project_id == project_id))
    await session.execute(delete(AssumptionEdge).where(AssumptionEdge.project_id == project_id))
    await session.execute(delete(Assumption).where(Assumption.project_id == project_id))
    await session.execute(delete(Run).where(Run.project_id == project_id))
    await session.execute(delete(Project).where(Project.id == project_id))
    await session.commit()


async def request_account_deletion(session: AsyncSession, user_id: str) -> User:
    user = await session.get(User, user_id)
    if not user:
        raise ValueError("user not found")
    user.deletion_requested_at = datetime.now(timezone.utc)
    user.is_active = False
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def delete_user_account(session: AsyncSession, user_id: str) -> None:
    project_ids = (
        await session.execute(select(Project.id).where(Project.user_id == user_id))
    ).scalars().all()
    for project_id in project_ids:
        await delete_project_data(session, project_id)
    await session.execute(delete(UsageRecord).where(UsageRecord.user_id == user_id))
    from app.models import APIKey

    await session.execute(delete(APIKey).where(APIKey.user_id == user_id))
    await session.execute(delete(User).where(User.id == user_id))
    await session.commit()


async def purge_retention_data(session: AsyncSession) -> dict[str, int]:
    now = datetime.now(timezone.utc)
    raw_cutoff = now - timedelta(days=settings.data_retention_days_raw)
    summary_cutoff = now - timedelta(days=settings.data_retention_days_summaries)
    metrics_cutoff = now - timedelta(days=settings.data_retention_days_metrics)
    deletion_cutoff = now - timedelta(days=settings.account_deletion_grace_days)

    run_events_deleted = (
        await session.execute(delete(RunEvent).where(RunEvent.created_at < raw_cutoff))
    ).rowcount or 0

    usage_deleted = (
        await session.execute(delete(UsageRecord).where(UsageRecord.created_at < metrics_cutoff))
    ).rowcount or 0

    old_projects = (
        await session.execute(select(Project.id).where(Project.created_at < summary_cutoff))
    ).scalars().all()
    summaries_purged = 0
    for project_id in old_projects:
        await session.execute(delete(Score).where(Score.project_id == project_id))
        await session.execute(delete(Critique).where(Critique.project_id == project_id))
        await session.execute(delete(Simulation).where(Simulation.project_id == project_id))
        await session.execute(delete(Reconstruction).where(Reconstruction.project_id == project_id))
        summaries_purged += 1

    pending_users = (
        await session.execute(
            select(User.id).where(
                User.deletion_requested_at.is_not(None),
                User.deletion_requested_at < deletion_cutoff,
            )
        )
    ).scalars().all()
    accounts_deleted = 0
    for user_id in pending_users:
        await delete_user_account(session, user_id)
        accounts_deleted += 1

    await session.execute(
        update(Project)
        .where(Project.created_at < raw_cutoff)
        .values(input_text="[retention redacted]")
    )
    await session.commit()

    return {
        "run_events_deleted": run_events_deleted,
        "usage_records_deleted": usage_deleted,
        "summary_projects_purged": summaries_purged,
        "accounts_deleted": accounts_deleted,
    }

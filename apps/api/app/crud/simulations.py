from __future__ import annotations

from typing import Any, Iterable

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Simulation


async def create_simulation(session: AsyncSession, project_id: str, scenario: str, likelihood: int | None = None, impact: int | None = None, affected_assumptions: list[str] | None = None) -> Simulation:
    s = Simulation(project_id=project_id, scenario=scenario, likelihood=likelihood, impact=impact, affected_assumptions_json=affected_assumptions)
    session.add(s)
    await session.commit()
    await session.refresh(s)
    return s


async def list_simulations_for_project(
    session: AsyncSession,
    project_id: str,
    *,
    limit: int,
    cursor: str | None = None,
):
    from app.core.pagination import paginate_by_id

    stmt = select(Simulation).where(Simulation.project_id == project_id)
    return await paginate_by_id(session, stmt, id_column=Simulation.id, limit=limit, cursor=cursor)

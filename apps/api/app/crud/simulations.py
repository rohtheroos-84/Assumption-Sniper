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


async def get_simulations_for_project(session: AsyncSession, project_id: str):
    q = select(Simulation).where(Simulation.project_id == project_id)
    r = await session.execute(q)
    return r.scalars().all()

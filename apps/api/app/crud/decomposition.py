from __future__ import annotations

from typing import Any
from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Decomposition


async def create_decomposition(session: AsyncSession, project_id: str, run_id: str | None, output: dict[str, Any]) -> Decomposition:
    d = Decomposition(project_id=project_id, run_id=run_id, output_json=output)
    session.add(d)
    await session.commit()
    await session.refresh(d)
    return d


async def get_decompositions_for_project(session: AsyncSession, project_id: str):
    q = select(Decomposition).where(Decomposition.project_id == project_id)
    r = await session.execute(q)
    return r.scalars().all()

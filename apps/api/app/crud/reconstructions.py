from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Reconstruction


async def create_reconstruction(session: AsyncSession, project_id: str, rebuilt_idea: str, key_changes: list[str] | None = None, risk_reductions: list[str] | None = None) -> Reconstruction:
    r = Reconstruction(project_id=project_id, rebuilt_idea=rebuilt_idea, key_changes_json=key_changes, risk_reductions_json=risk_reductions)
    session.add(r)
    await session.commit()
    await session.refresh(r)
    return r


async def list_reconstructions_for_project(
    session: AsyncSession,
    project_id: str,
    *,
    limit: int,
    cursor: str | None = None,
):
    from app.core.pagination import paginate_by_id

    stmt = select(Reconstruction).where(Reconstruction.project_id == project_id)
    return await paginate_by_id(session, stmt, id_column=Reconstruction.id, limit=limit, cursor=cursor)

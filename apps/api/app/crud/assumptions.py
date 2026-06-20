from __future__ import annotations

from typing import Any, Iterable

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Assumption, AssumptionEdge


async def create_assumptions_and_edges(session: AsyncSession, project_id: str, items: Iterable[dict[str, Any]]):
    # items are dicts matching AssumptionItem: assumption_id?, assumption_text, category, parent_id?, depth
    created = []
    id_map: dict[str, str] = {}

    for it in items:
        aid = it.get("assumption_id") or None
        a = Assumption(
            id=aid,
            project_id=project_id,
            assumption_text=it["assumption_text"],
            category=it.get("category"),
            confidence_score=None,
            impact_score=None,
        )
        session.add(a)
        created.append(a)

    await session.flush()

    # create edges where parent_id provided
    for it, a in zip(items, created):
        parent = it.get("parent_id")
        if parent:
            edge = AssumptionEdge(
                project_id=project_id,
                parent_id=parent,
                child_id=a.id,
                depth=it.get("depth", 1),
            )
            session.add(edge)

    await session.commit()

    # refresh created objects
    for a in created:
        await session.refresh(a)

    return created


async def list_assumptions_for_project(
    session: AsyncSession,
    project_id: str,
    *,
    limit: int,
    cursor: str | None = None,
):
    from app.core.pagination import paginate_by_id

    stmt = select(Assumption).where(Assumption.project_id == project_id)
    return await paginate_by_id(session, stmt, id_column=Assumption.id, limit=limit, cursor=cursor)

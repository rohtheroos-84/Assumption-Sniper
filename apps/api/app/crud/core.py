from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, Run, Assumption


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

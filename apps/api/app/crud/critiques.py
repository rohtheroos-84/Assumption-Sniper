from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Critique


async def create_critique(session: AsyncSession, project_id: str, assumption_id: str, critique_text: str, severity: int | None = None, rationale: str | None = None) -> Critique:
    c = Critique(project_id=project_id, assumption_id=assumption_id, critique_text=critique_text, severity=severity)
    session.add(c)
    await session.commit()
    await session.refresh(c)
    return c

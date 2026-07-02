from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import AnalyticsEvent, BetaInvite, Feedback

settings = get_settings()


def configured_invite_codes() -> set[str]:
    return {code.strip() for code in settings.beta_invite_codes.split(",") if code.strip()}


async def ensure_default_invites(session: AsyncSession) -> None:
    for code in configured_invite_codes():
        existing = await session.execute(select(BetaInvite).where(BetaInvite.code == code))
        if existing.scalars().first():
            continue
        cohort = "founders" if "founder" in code else "pm"
        session.add(BetaInvite(code=code, cohort=cohort, max_uses=50))
    await session.commit()


async def validate_invite(session: AsyncSession, code: str) -> bool:
    if not settings.beta_enabled:
        return True
    if code in configured_invite_codes():
        row = await session.execute(select(BetaInvite).where(BetaInvite.code == code))
        invite = row.scalars().first()
        if invite and invite.uses < invite.max_uses:
            return True
        if not invite:
            return True
    row = await session.execute(select(BetaInvite).where(BetaInvite.code == code))
    invite = row.scalars().first()
    if not invite:
        return False
    return invite.uses < invite.max_uses


async def consume_invite(session: AsyncSession, code: str) -> None:
    row = await session.execute(select(BetaInvite).where(BetaInvite.code == code))
    invite = row.scalars().first()
    if invite:
        invite.uses += 1
        session.add(invite)
        await session.commit()


async def create_feedback(
    session: AsyncSession,
    *,
    message: str,
    category: str = "general",
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    page: Optional[str] = None,
    rating: Optional[int] = None,
    meta: Optional[dict] = None,
) -> Feedback:
    item = Feedback(
        user_id=user_id,
        session_id=session_id,
        category=category,
        message=message,
        page=page,
        rating=rating,
        meta_json=meta or {},
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


async def list_feedback(session: AsyncSession, *, limit: int = 100) -> list[Feedback]:
    q = await session.execute(select(Feedback).order_by(Feedback.created_at.desc()).limit(limit))
    return list(q.scalars().all())


async def record_analytics_events(session: AsyncSession, events: list[dict]) -> int:
    count = 0
    for event in events:
        session.add(
            AnalyticsEvent(
                session_id=event["session_id"],
                user_id=event.get("user_id"),
                event_name=event["event_name"],
                page=event.get("page"),
                payload_json=event.get("payload") or {},
            )
        )
        count += 1
    await session.commit()
    return count

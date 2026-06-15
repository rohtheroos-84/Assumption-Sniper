from __future__ import annotations

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models import User, APIKey, UsageRecord


async def create_user(session: AsyncSession, email: str, password: Optional[str] = None) -> User:
    user = User(email=email)
    if password:
        user.hashed_password = hash_password(password)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    q = await session.execute(select(User).where(User.email == email))
    return q.scalars().first()


async def get_user_by_id(session: AsyncSession, user_id: str) -> Optional[User]:
    q = await session.execute(select(User).where(User.id == user_id))
    return q.scalars().first()


async def create_api_key(session: AsyncSession, user_id: str, key: str, label: Optional[str] = None) -> APIKey:
    api = APIKey(user_id=user_id, key=key, label=label)
    session.add(api)
    await session.commit()
    await session.refresh(api)
    return api


async def get_api_key_by_value(session: AsyncSession, key_value: str) -> Optional[APIKey]:
    q = await session.execute(select(APIKey).where(APIKey.key == key_value))
    return q.scalars().first()


async def list_api_keys(session: AsyncSession, user_id: str) -> list[APIKey]:
    q = await session.execute(select(APIKey).where(APIKey.user_id == user_id))
    return q.scalars().all()


async def revoke_api_key(session: AsyncSession, key_id: str) -> Optional[APIKey]:
    api = await session.get(APIKey, key_id)
    if not api:
        return None
    api.revoked = True
    session.add(api)
    await session.commit()
    await session.refresh(api)
    return api


async def record_usage(session: AsyncSession, user_id: Optional[str], project_id: Optional[str], run_id: Optional[str], tokens: int = 0, cost_usd: float = 0.0) -> UsageRecord:
    usage = UsageRecord(user_id=user_id, project_id=project_id, run_id=run_id, tokens=tokens, cost_usd=cost_usd)
    session.add(usage)
    await session.commit()
    await session.refresh(usage)
    return usage

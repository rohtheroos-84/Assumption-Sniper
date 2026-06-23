from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_api_key, hash_api_key, hash_password
from app.models import APIKey, UsageRecord, User


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


async def create_api_key(
    session: AsyncSession,
    user_id: str,
    *,
    label: Optional[str] = None,
    rotated_from_id: Optional[str] = None,
) -> tuple[APIKey, str]:
    plain_key = generate_api_key()
    api = APIKey(
        user_id=user_id,
        key_hash=hash_api_key(plain_key),
        key_prefix=plain_key[:8],
        label=label,
        rotated_from_id=rotated_from_id,
    )
    session.add(api)
    await session.commit()
    await session.refresh(api)
    return api, plain_key


async def get_api_key_by_value(session: AsyncSession, key_value: str) -> Optional[APIKey]:
    q = await session.execute(select(APIKey).where(APIKey.key_hash == hash_api_key(key_value)))
    return q.scalars().first()


async def list_api_keys(session: AsyncSession, user_id: str) -> list[APIKey]:
    q = await session.execute(select(APIKey).where(APIKey.user_id == user_id).order_by(APIKey.created_at.desc()))
    return q.scalars().all()


async def revoke_api_key(session: AsyncSession, key_id: str, user_id: str) -> Optional[APIKey]:
    api = await session.get(APIKey, key_id)
    if not api or api.user_id != user_id:
        return None
    api.revoked = True
    session.add(api)
    await session.commit()
    await session.refresh(api)
    return api


async def rotate_api_key(session: AsyncSession, key_id: str, user_id: str) -> tuple[APIKey, str] | None:
    api = await session.get(APIKey, key_id)
    if not api or api.user_id != user_id or api.revoked:
        return None
    api.revoked = True
    session.add(api)
    await session.commit()
    return await create_api_key(session, user_id, label=api.label, rotated_from_id=api.id)


async def record_usage(
    session: AsyncSession,
    user_id: Optional[str],
    project_id: Optional[str],
    run_id: Optional[str],
    tokens: int = 0,
    cost_usd: float = 0.0,
) -> UsageRecord:
    usage = UsageRecord(user_id=user_id, project_id=project_id, run_id=run_id, tokens=tokens, cost_usd=cost_usd)
    session.add(usage)
    await session.commit()
    await session.refresh(usage)
    return usage

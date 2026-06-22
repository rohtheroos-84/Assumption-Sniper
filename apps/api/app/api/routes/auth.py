from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_current_user
from app.api.request_context import audit_context
from app.crud import audit as audit_crud
from app.crud import auth as auth_crud
from app.core.security import create_access_token, verify_password
from app.db import get_session
from app.models import UsageRecord, User

router = APIRouter(prefix="/auth")


class RegisterIn(BaseModel):
    email: EmailStr
    password: Optional[str]


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=TokenOut)
async def register(payload: RegisterIn, request: Request, session: AsyncSession = Depends(get_session)):
    existing = await auth_crud.get_user_by_email(session, payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    user = await auth_crud.create_user(session, payload.email, payload.password)
    token = create_access_token(user.id)
    ctx = audit_context(request)
    await audit_crud.record_audit(
        session,
        actor_id=user.id,
        action="auth.register",
        resource_type="user",
        resource_id=user.id,
        **ctx,
    )
    return TokenOut(access_token=token)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn, request: Request, session: AsyncSession = Depends(get_session)):
    user = await auth_crud.get_user_by_email(session, payload.email)
    ctx = audit_context(request)
    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        await audit_crud.record_audit(
            session,
            actor_id=user.id if user else None,
            action="auth.login",
            resource_type="user",
            resource_id=user.id if user else None,
            status="failed",
            **ctx,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account inactive or pending deletion")
    token = create_access_token(user.id)
    await audit_crud.record_audit(
        session,
        actor_id=user.id,
        action="auth.login",
        resource_type="user",
        resource_id=user.id,
        **ctx,
    )
    return TokenOut(access_token=token)


class APIKeyOut(BaseModel):
    id: str
    key: str
    key_prefix: str
    label: Optional[str]


class APIKeyListItem(BaseModel):
    id: str
    key_prefix: str
    label: Optional[str]
    revoked: bool
    created_at: str | None


@router.post("/apikey", response_model=APIKeyOut)
async def create_apikey(
    request: Request,
    label: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    api, plain_key = await auth_crud.create_api_key(session, user_id=current_user.id, label=label)
    ctx = audit_context(request)
    await audit_crud.record_audit(
        session,
        actor_id=current_user.id,
        action="auth.apikey.create",
        resource_type="api_key",
        resource_id=api.id,
        meta={"key_prefix": api.key_prefix},
        **ctx,
    )
    return APIKeyOut(id=api.id, key=plain_key, key_prefix=api.key_prefix, label=api.label)


@router.get("/apikeys", response_model=list[APIKeyListItem])
async def list_apikeys(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    rows = await auth_crud.list_api_keys(session, current_user.id)
    return [
        APIKeyListItem(
            id=row.id,
            key_prefix=row.key_prefix,
            label=row.label,
            revoked=row.revoked,
            created_at=row.created_at.isoformat() if row.created_at else None,
        )
        for row in rows
    ]


@router.post("/apikeys/{key_id}/revoke")
async def revoke_apikey(
    key_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    api = await auth_crud.revoke_api_key(session, key_id, current_user.id)
    if not api:
        raise HTTPException(status_code=404, detail="api key not found")
    ctx = audit_context(request)
    await audit_crud.record_audit(
        session,
        actor_id=current_user.id,
        action="auth.apikey.revoke",
        resource_type="api_key",
        resource_id=api.id,
        **ctx,
    )
    return {"id": api.id, "revoked": True}


@router.post("/apikeys/{key_id}/rotate", response_model=APIKeyOut)
async def rotate_apikey(
    key_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
):
    rotated = await auth_crud.rotate_api_key(session, key_id, current_user.id)
    if not rotated:
        raise HTTPException(status_code=404, detail="api key not found")
    api, plain_key = rotated
    ctx = audit_context(request)
    await audit_crud.record_audit(
        session,
        actor_id=current_user.id,
        action="auth.apikey.rotate",
        resource_type="api_key",
        resource_id=api.id,
        meta={"rotated_from_id": key_id},
        **ctx,
    )
    return APIKeyOut(id=api.id, key=plain_key, key_prefix=api.key_prefix, label=api.label)


@router.get("/usage")
async def get_usage(session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_active_user)):
    q = await session.execute(
        select(UsageRecord)
        .where(UsageRecord.user_id == current_user.id)
        .order_by(UsageRecord.created_at.desc())
        .limit(100)
    )
    rows = q.scalars().all()
    return [
        {
            "id": r.id,
            "project_id": r.project_id,
            "run_id": r.run_id,
            "tokens": r.tokens,
            "cost_usd": float(r.cost_usd) if r.cost_usd is not None else None,
            "created_at": str(r.created_at),
        }
        for r in rows
    ]

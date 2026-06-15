from __future__ import annotations

from typing import Optional
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.crud import auth as auth_crud
from app.core.security import verify_password, create_access_token
from app.models import User
from app.api.deps import get_current_user
from app.models import UsageRecord
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth")


class RegisterIn(BaseModel):
    email: EmailStr
    password: Optional[str]


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=TokenOut)
async def register(payload: RegisterIn, session: AsyncSession = Depends(get_session)):
    existing = await auth_crud.get_user_by_email(session, payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    user = await auth_crud.create_user(session, payload.email, payload.password)
    token = create_access_token(user.id)
    return TokenOut(access_token=token)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn, session: AsyncSession = Depends(get_session)):
    user = await auth_crud.get_user_by_email(session, payload.email)
    if not user or not user.hashed_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(user.id)
    return TokenOut(access_token=token)


class APIKeyOut(BaseModel):
    key: str
    label: Optional[str]


@router.post("/apikey", response_model=APIKeyOut)
async def create_apikey(label: Optional[str] = None, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    api_key = secrets.token_urlsafe(32)
    api = await auth_crud.create_api_key(session, user_id=current_user.id, key=api_key, label=label)
    return APIKeyOut(key=api.key, label=api.label)


@router.get('/usage')
async def get_usage(session: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    q = await session.execute(select(UsageRecord).where(UsageRecord.user_id == current_user.id).order_by(UsageRecord.created_at.desc()).limit(100))
    rows = q.scalars().all()
    return [ { 'id': r.id, 'project_id': r.project_id, 'run_id': r.run_id, 'tokens': r.tokens, 'cost_usd': float(r.cost_usd) if r.cost_usd is not None else None, 'created_at': str(r.created_at) } for r in rows ]

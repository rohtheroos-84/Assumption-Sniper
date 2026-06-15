from __future__ import annotations

from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db import get_session
from app.crud import auth as auth_crud


async def get_current_user(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_session),
):
    # API key header has precedence
    if x_api_key:
        api = await auth_crud.get_api_key_by_value(session, x_api_key)
        if api and not api.revoked:
            user = await auth_crud.get_user_by_id(session, api.user_id)
            if user:
                return user

    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            try:
                payload = decode_access_token(token)
            except Exception:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
            sub = payload.get("sub")
            if not sub:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
            user = await auth_crud.get_user_by_id(session, sub)
            if user:
                return user

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

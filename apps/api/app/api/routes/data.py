from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.api.request_context import audit_context
from app.crud import audit as audit_crud
from app.crud import retention as retention_crud
from app.crud.core import get_project
from app.db import get_session
from app.models import User

router = APIRouter(prefix="/data", tags=["data"])


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    project = await get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="project not found")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="forbidden")
    await retention_crud.delete_project_data(session, project_id)
    ctx = audit_context(request)
    await audit_crud.record_audit(
        session,
        actor_id=current_user.id,
        action="data.project.delete",
        resource_type="project",
        resource_id=project_id,
        **ctx,
    )
    return {"project_id": project_id, "status": "deleted"}


@router.delete("/account")
async def delete_account(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    user = await retention_crud.request_account_deletion(session, current_user.id)
    ctx = audit_context(request)
    await audit_crud.record_audit(
        session,
        actor_id=current_user.id,
        action="data.account.delete_requested",
        resource_type="user",
        resource_id=user.id,
        meta={"deletion_requested_at": user.deletion_requested_at.isoformat() if user.deletion_requested_at else None},
        **ctx,
    )
    return {
        "user_id": user.id,
        "status": "deletion_scheduled",
        "message": "Account deletion will complete after the retention grace period.",
    }

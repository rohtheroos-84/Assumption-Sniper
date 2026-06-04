from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.ai.schemas import AIRequest
from app.ai.service import build_ai_service
from app.crud.decomposition import create_decomposition
from app.db import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.crud.assumptions import create_assumptions_and_edges
from app.ai.schemas_runtime import AssumptionsOutput

router = APIRouter()
service = build_ai_service()


@router.post("/ai/preview")
async def ai_preview(request: AIRequest):
    if request.dry_run:
        return {
            "task": request.task,
            "dry_run": True,
            "input_text": request.input_text,
            "max_depth": request.max_depth,
        }

    try:
        result = await service.run(request)
        return result.model_dump()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/decompose")
async def decompose(
    request: AIRequest, session: AsyncSession = Depends(get_session)
):
    if request.task != request.task.__class__.decomposition:
        # normalize to decomposition task
        request.task = request.task.__class__.decomposition

    # ensure a run exists; if not, create one
    if not request.run_id:
        from app.crud.core import create_run

        run = await create_run(session, request.project_id)
        request.run_id = run.id

    try:
        result = await service.run(request)
        # persist decomposition
        await create_decomposition(session, request.project_id, request.run_id, result.parsed_output)
        return result.model_dump()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/assumptions")
async def extract_assumptions(request: AIRequest, session: AsyncSession = Depends(get_session)):
    if request.task != request.task.__class__.assumptions:
        request.task = request.task.__class__.assumptions

    if not request.run_id:
        from app.crud.core import create_run

        run = await create_run(session, request.project_id)
        request.run_id = run.id

    try:
        result = await service.run(request)
        # parse assumptions output
        parsed = result.parsed_output
        # validate shape loosely
        try:
            ao = AssumptionsOutput.model_validate(parsed)
        except Exception:
            ao = AssumptionsOutput(assumptions=[])

        items = [item.model_dump() for item in ao.assumptions]
        created = await create_assumptions_and_edges(session, request.project_id, items)
        return {"created": [ {"id": a.id, "text": a.assumption_text} for a in created ], "raw": result.model_dump()}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

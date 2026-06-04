from __future__ import annotations

from fastapi import APIRouter, HTTPException, BackgroundTasks

from app.ai.schemas import AIRequest
from app.ai.service import build_ai_service
from app.crud.decomposition import create_decomposition
from app.db import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.crud.assumptions import create_assumptions_and_edges
from app.ai.schemas_runtime import AssumptionsOutput, ClassificationOutput
from app.ai.schemas import AITask
from app.db import AsyncSessionLocal
import json

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
async def extract_assumptions(
    request: AIRequest,
    session: AsyncSession = Depends(get_session),
    background: bool = False,
    background_tasks: BackgroundTasks | None = None,
):
    if request.task != request.task.__class__.assumptions:
        request.task = request.task.__class__.assumptions

    if not request.run_id:
        from app.crud.core import create_run

        run = await create_run(session, request.project_id)
        request.run_id = run.id

    async def _run_and_persist(req: AIRequest, run_id: str | None):
        r = await service.run(req)
        parsed = r.parsed_output
        try:
            ao = AssumptionsOutput.model_validate(parsed)
        except Exception:
            ao = AssumptionsOutput(assumptions=[])

        # items list of dicts
        items = [item.model_dump() for item in ao.assumptions]

        # if any item missing category, call classifier
        missing = [it for it in items if not it.get("category")]
        if missing:
            # build classification input as json array of strings
            texts = [it["assumption_text"] for it in items]
            classify_req = AIRequest(task=AITask.assumption_classification, input_text=json.dumps(texts), project_id=req.project_id, run_id=req.run_id, dry_run=False)
            cr = await service.run(classify_req)
            try:
                co = ClassificationOutput.model_validate(cr.parsed_output)
                mapping = {c.assumption_text: c.category for c in co.classifications}
                for it in items:
                    if not it.get("category"):
                        it["category"] = mapping.get(it["assumption_text"], "other")
            except Exception:
                # ignore classification failures
                pass

        # persist
        async with AsyncSessionLocal() as s:
            await create_assumptions_and_edges(s, req.project_id, items)

        return r

    try:
        if background:
            # schedule background run and return run id
            if not request.run_id:
                from app.crud.core import create_run

                run = await create_run(session, request.project_id)
                request.run_id = run.id

            if background_tasks is None:
                raise HTTPException(status_code=400, detail="background tasks not provided")

            background_tasks.add_task(_run_and_persist, request, request.run_id)
            return {"run_id": request.run_id, "status": "queued"}

        # synchronous
        result = await _run_and_persist(request, request.run_id)
        return result.model_dump()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

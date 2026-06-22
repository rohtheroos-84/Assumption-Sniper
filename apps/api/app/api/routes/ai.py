from __future__ import annotations

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends

from app.ai.schemas import AIRequest, DebateRequest
from app.ai.service import build_ai_service
from app.api.deps import get_current_active_user
from app.models import User
from app.ai.batching import chunk_items
from app.core.config import get_settings
from app.crud.decomposition import create_decomposition
from app.db import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.crud.assumptions import create_assumptions_and_edges
from app.ai.schemas_runtime import AssumptionsOutput, ClassificationOutput
from app.ai.schemas import AITask
from app.db import AsyncSessionLocal
import json
from app.crud.critiques import create_critique
from app.ai.schemas_runtime import CritiquesOutput
from app.crud.core import create_assumption
from app.ai.schemas_runtime import SimulationsOutput
from app.crud.simulations import create_simulation
from app.crud.scores import compute_and_persist_scores
from app.crud.reconstructions import create_reconstruction
from app.ai.schemas_runtime import ReconstructionOutput, DebateOutput

router = APIRouter()
service = build_ai_service()
settings = get_settings()


async def _classify_missing_categories(items: list[dict], *, project_id: str, run_id: str | None) -> None:
    texts = [it["assumption_text"] for it in items if not it.get("category")]
    if not texts:
        return
    mapping: dict[str, str] = {}
    for batch in chunk_items(texts, settings.ai_batch_size):
        classify_req = AIRequest(
            task=AITask.assumption_classification,
            input_text=json.dumps(batch),
            project_id=project_id,
            run_id=run_id,
            dry_run=False,
        )
        cr = await service.run(classify_req)
        try:
            co = ClassificationOutput.model_validate(cr.parsed_output)
            for c in co.classifications:
                mapping[c.assumption_text] = c.category
        except Exception:
            continue
    for it in items:
        if not it.get("category"):
            it["category"] = mapping.get(it["assumption_text"], "other")


@router.post("/ai/preview")
async def ai_preview(request: AIRequest, current_user: User = Depends(get_current_active_user)):
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
    request: AIRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
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
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    background: bool = False,
    current_user: User = Depends(get_current_active_user),
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

        # if any item missing category, classify in safe batches
        missing = [it for it in items if not it.get("category")]
        if missing:
            await _classify_missing_categories(items, project_id=req.project_id, run_id=req.run_id)

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

            background_tasks.add_task(_run_and_persist, request, request.run_id)
            return {"run_id": request.run_id, "status": "queued"}

        # synchronous
        result = await _run_and_persist(request, request.run_id)
        return result.model_dump()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc



@router.post("/critiques")
async def generate_critiques(
    request: AIRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    background: bool = False,
    assumption_id: str | None = None,
):
    if request.task != request.task.__class__.critique:
        request.task = request.task.__class__.critique

    if not request.run_id:
        from app.crud.core import create_run

        run = await create_run(session, request.project_id)
        request.run_id = run.id

    async def _run_and_persist_critiques(req: AIRequest):
        r = await service.run(req)
        parsed = r.parsed_output
        try:
            co = CritiquesOutput.model_validate(parsed)
        except Exception:
            co = CritiquesOutput(critiques=[])

        created = []
        async with AsyncSessionLocal() as s:
            for it in co.critiques:
                a_id = it.assumption_id or assumption_id
                if not a_id:
                    # create the assumption record if missing
                    a = await create_assumption(s, req.project_id, it.critique_text)
                    a_id = a.id

                severity = getattr(it, "severity", None)
                if severity is None:
                    # fallback heuristic
                    severity = min(100, max(0, len(it.critique_text) // 5))

                c = await create_critique(s, req.project_id, a_id, it.critique_text, severity=severity)
                created.append(c)

        return {"created": [{"id": c.id, "severity": c.severity} for c in created], "raw": r.model_dump()}

    try:
        if background:
            background_tasks.add_task(_run_and_persist_critiques, request)
            return {"run_id": request.run_id, "status": "queued"}

        return await _run_and_persist_critiques(request)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/debate")
async def debate_review(
    request: DebateRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    try:
        result = await service.debate(request)
        return result.model_dump()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc



@router.post("/simulations")
async def generate_simulations(
    request: AIRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    background: bool = False,
    current_user: User = Depends(get_current_active_user),
):
    if request.task != request.task.__class__.simulation:
        request.task = request.task.__class__.simulation

    if not request.run_id:
        from app.crud.core import create_run

        run = await create_run(session, request.project_id)
        request.run_id = run.id

    async def _run_and_persist_simulations(req: AIRequest):
        r = await service.run(req)
        parsed = r.parsed_output
        try:
            so = SimulationsOutput.model_validate(parsed)
        except Exception:
            so = SimulationsOutput(simulations=[])

        created = []
        async with AsyncSessionLocal() as s:
            for it in so.simulations:
                likelihood = getattr(it, "likelihood", None)
                impact = getattr(it, "impact", None)
                affected = getattr(it, "affected_assumptions", [])
                sim = await create_simulation(s, req.project_id, it.scenario, likelihood=likelihood, impact=impact, affected_assumptions=affected)
                created.append(sim)

        return {"created": [{"id": sim.id, "scenario": sim.scenario} for sim in created], "raw": r.model_dump()}

    try:
        if background:
            background_tasks.add_task(_run_and_persist_simulations, request)
            return {"run_id": request.run_id, "status": "queued"}

        return await _run_and_persist_simulations(request)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/reconstructions")
async def generate_reconstruction(
    request: AIRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    background: bool = False,
    current_user: User = Depends(get_current_active_user),
):
    if request.task != request.task.__class__.reconstruction:
        request.task = request.task.__class__.reconstruction

    if not request.run_id:
        from app.crud.core import create_run

        run = await create_run(session, request.project_id)
        request.run_id = run.id

    async def _run_and_persist_recon(req: AIRequest):
        r = await service.run(req)
        parsed = r.parsed_output
        try:
            ro = ReconstructionOutput.model_validate(parsed)
        except Exception:
            ro = ReconstructionOutput(rebuilt_idea="", key_changes=[], risk_reductions=[], new_assumptions=[])

        async with AsyncSessionLocal() as s:
            rec = await create_reconstruction(s, req.project_id, ro.rebuilt_idea, key_changes=ro.key_changes, risk_reductions=ro.risk_reductions)

        return {"id": rec.id, "rebuilt_idea": rec.rebuilt_idea, "raw": r.model_dump()}

    try:
        if background:
            background_tasks.add_task(_run_and_persist_recon, request)
            return {"run_id": request.run_id, "status": "queued"}

        return await _run_and_persist_recon(request)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/scores")
async def compute_scores(
    request: AIRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    background: bool = False,
    current_user: User = Depends(get_current_active_user),
):
    if not request.project_id:
        raise HTTPException(status_code=400, detail="project_id required")

    async def _compute():
        async with AsyncSessionLocal() as s:
            scores = await compute_and_persist_scores(s, request.project_id)
        return scores

    try:
        if background:
            background_tasks.add_task(_compute)
            return {"project_id": request.project_id, "status": "queued"}

        scores = await _compute()
        return {"created": [{"id": sc.id, "assumption_id": sc.assumption_id, "risk_score": sc.risk_score} for sc in scores]}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

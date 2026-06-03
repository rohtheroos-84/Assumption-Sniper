from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.ai.schemas import AIRequest
from app.ai.service import build_ai_service

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

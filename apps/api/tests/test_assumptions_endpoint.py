import asyncio
from types import SimpleNamespace

import pytest

from app.ai.schemas import AIRequest, AITask
from app.ai.schemas import PromptMetadata
from app.ai.schemas import AIResult
from app.ai.schemas_runtime import AssumptionsOutput

from app.api.routes import ai as ai_routes


class DummySession:
    pass


@pytest.mark.asyncio
async def test_extract_assumptions_sync(monkeypatch):
    # prepare fake AI result
    parsed = {"assumptions": [{"assumption_text": "users want free delivery", "category": ""}]}
    metadata = PromptMetadata(prompt_version="v1", experiment_id="exp", model="m", fallback_model=None, cached=False, safety_blocked=False)
    ai_result = AIResult(task=AITask.assumptions, metadata=metadata, raw_output="", parsed_output=parsed, usage={}, warnings=[])

    async def fake_run(req):
        return ai_result

    async def fake_create_assumptions_and_edges(session, project_id, items):
        return [SimpleNamespace(id="a1", assumption_text=items[0]["assumption_text"])]

    async def fake_create_run(session, project_id):
        return SimpleNamespace(id="r1")

    monkeypatch.setattr(ai_routes, "service", SimpleNamespace(run=fake_run))
    monkeypatch.setattr("app.api.routes.ai.create_assumptions_and_edges", fake_create_assumptions_and_edges)
    monkeypatch.setattr("app.crud.core.create_run", fake_create_run)

    req = AIRequest(task=AITask.assumptions, input_text="idea", project_id="p1", dry_run=False)
    res = await ai_routes.extract_assumptions(req, session=DummySession())
    assert "raw" in res
    assert "created" in res
    assert res["created"][0]["text"] == "users want free delivery"


@pytest.mark.asyncio
async def test_extract_assumptions_background(monkeypatch):
    async def fake_run(req):
        return AIResult(task=AITask.assumptions, metadata=PromptMetadata(prompt_version="v1", experiment_id="exp", model="m", fallback_model=None, cached=False, safety_blocked=False), raw_output="", parsed_output={"assumptions": []}, usage={}, warnings=[])

    async def fake_create_run(session, project_id):
        return SimpleNamespace(id="r-bg")

    monkeypatch.setattr(ai_routes, "service", SimpleNamespace(run=fake_run))
    monkeypatch.setattr("app.crud.core.create_run", fake_create_run)

    req = AIRequest(task=AITask.assumptions, input_text="idea", project_id="p1", dry_run=False)
    from fastapi import BackgroundTasks

    bg = BackgroundTasks()
    res = await ai_routes.extract_assumptions(req, session=DummySession(), background=True, background_tasks=bg)
    assert res["status"] == "queued"
    assert "run_id" in res
*** End Patch
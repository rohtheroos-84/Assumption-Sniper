import pytest
from types import SimpleNamespace

from app.api.routes import ai as ai_routes
from app.ai.schemas import AIRequest, AITask
from app.ai.schemas import AIResult, PromptMetadata


class DummySession:
    pass


@pytest.mark.asyncio
async def test_generate_critiques_sync(monkeypatch):
    parsed = {"critiques": [{"critique_text": "this will fail due to ops cost", "assumption_id": None, "severity": 80}]}
    metadata = PromptMetadata(prompt_version="v1", experiment_id="exp", model="m", fallback_model=None, cached=False, safety_blocked=False)
    ai_result = AIResult(task=AITask.critique, metadata=metadata, raw_output="", parsed_output=parsed, usage={}, warnings=[])

    async def fake_run(req):
        return ai_result

    async def fake_create_assumption(session, project_id, text):
        return SimpleNamespace(id="a-new")

    async def fake_create_critique(session, project_id, assumption_id, critique_text, severity=None):
        return SimpleNamespace(id="c1", severity=severity)

    monkeypatch.setattr(ai_routes, "service", SimpleNamespace(run=fake_run))
    monkeypatch.setattr("app.crud.core.create_assumption", fake_create_assumption)
    monkeypatch.setattr("app.crud.critiques.create_critique", fake_create_critique)

    req = AIRequest(task=AITask.critique, input_text="assumption: xyz", project_id="p1", dry_run=False)
    res = await ai_routes.generate_critiques(req, session=DummySession())
    assert "created" in res
    assert res["created"][0]["severity"] == 80


@pytest.mark.asyncio
async def test_generate_critiques_background(monkeypatch):
    async def fake_run(req):
        return AIResult(task=AITask.critique, metadata=PromptMetadata(prompt_version="v1", experiment_id="exp", model="m", fallback_model=None, cached=False, safety_blocked=False), raw_output="", parsed_output={"critiques": []}, usage={}, warnings=[])

    async def fake_create_run(session, project_id):
        return SimpleNamespace(id="r-bg")

    monkeypatch.setattr(ai_routes, "service", SimpleNamespace(run=fake_run))
    monkeypatch.setattr("app.crud.core.create_run", fake_create_run)

    req = AIRequest(task=AITask.critique, input_text="assumption: xyz", project_id="p1", dry_run=False)
    from fastapi import BackgroundTasks

    bg = BackgroundTasks()
    res = await ai_routes.generate_critiques(req, session=DummySession(), background=True, background_tasks=bg)
    assert res["status"] == "queued"
*** End Patch
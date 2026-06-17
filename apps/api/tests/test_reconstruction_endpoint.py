import pytest
from types import SimpleNamespace

from app.api.routes import ai as ai_routes
from app.ai.schemas import AIRequest, AITask
from app.ai.schemas import AIResult, PromptMetadata


class DummySession:
    pass


@pytest.mark.asyncio
async def test_generate_reconstruction_sync(monkeypatch):
    parsed = {"rebuilt_idea": "narrow to dorm buildings only", "key_changes": ["limit scope"], "risk_reductions": ["use campus drivers"]}
    metadata = PromptMetadata(prompt_version="v1", experiment_id="exp", model="m", fallback_model=None, cached=False, safety_blocked=False)
    ai_result = AIResult(task=AITask.reconstruction, metadata=metadata, raw_output="", parsed_output=parsed, usage={}, warnings=[])

    async def fake_run(req):
        return ai_result

    async def fake_create_reconstruction(session, project_id, rebuilt_idea, key_changes=None, risk_reductions=None):
        return SimpleNamespace(id="rec1", rebuilt_idea=rebuilt_idea)

    async def fake_create_run(session, project_id):
        return SimpleNamespace(id="r1")

    monkeypatch.setattr(ai_routes, "service", SimpleNamespace(run=fake_run))
    monkeypatch.setattr(ai_routes, "create_reconstruction", fake_create_reconstruction)
    monkeypatch.setattr("app.crud.core.create_run", fake_create_run)

    from fastapi import BackgroundTasks

    req = AIRequest(task=AITask.reconstruction, input_text="idea", project_id="p1", dry_run=False)
    res = await ai_routes.generate_reconstruction(req, BackgroundTasks(), session=DummySession())
    assert "id" in res
    assert res["rebuilt_idea"] == "narrow to dorm buildings only"


@pytest.mark.asyncio
async def test_generate_reconstruction_background(monkeypatch):
    async def fake_run(req):
        return AIResult(task=AITask.reconstruction, metadata=PromptMetadata(prompt_version="v1", experiment_id="exp", model="m", fallback_model=None, cached=False, safety_blocked=False), raw_output="", parsed_output={"rebuilt_idea":"","key_changes":[],"risk_reductions":[]}, usage={}, warnings=[])

    async def fake_create_run(session, project_id):
        return SimpleNamespace(id="r-bg")

    monkeypatch.setattr(ai_routes, "service", SimpleNamespace(run=fake_run))
    monkeypatch.setattr("app.crud.core.create_run", fake_create_run)

    req = AIRequest(task=AITask.reconstruction, input_text="idea", project_id="p1", dry_run=False)
    from fastapi import BackgroundTasks

    bg = BackgroundTasks()
    res = await ai_routes.generate_reconstruction(req, bg, session=DummySession(), background=True)
    assert res["status"] == "queued"

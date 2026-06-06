import pytest
from types import SimpleNamespace

from app.api.routes import ai as ai_routes
from app.ai.schemas import AIRequest, AITask


class DummySession:
    pass


@pytest.mark.asyncio
async def test_compute_scores_sync(monkeypatch):
    async def fake_compute(session, project_id):
        return [SimpleNamespace(id="s1", assumption_id="a1", risk_score=42)]

    monkeypatch.setattr("app.crud.scores.compute_and_persist_scores", fake_compute)

    req = AIRequest(task=AITask.assumptions, input_text="idea", project_id="p1", dry_run=False)
    res = await ai_routes.compute_scores(req, session=DummySession())
    assert "created" in res
    assert res["created"][0]["risk_score"] == 42


@pytest.mark.asyncio
async def test_compute_scores_background(monkeypatch):
    async def fake_compute(session, project_id):
        return []

    async def fake_create_run(session, project_id):
        return SimpleNamespace(id="r-bg")

    monkeypatch.setattr("app.crud.scores.compute_and_persist_scores", fake_compute)
    monkeypatch.setattr("app.crud.core.create_run", fake_create_run)

    req = AIRequest(task=AITask.assumptions, input_text="idea", project_id="p1", dry_run=False)
    from fastapi import BackgroundTasks

    bg = BackgroundTasks()
    res = await ai_routes.compute_scores(req, session=DummySession(), background=True, background_tasks=bg)
    assert res["status"] == "queued"
*** End Patch
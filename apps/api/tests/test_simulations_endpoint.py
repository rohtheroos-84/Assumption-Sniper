import pytest
from types import SimpleNamespace

from app.api.routes import ai as ai_routes
from app.ai.schemas import AIRequest, AITask
from app.ai.schemas import AIResult, PromptMetadata


class DummySession:
    pass


@pytest.mark.asyncio
async def test_generate_simulations_sync(monkeypatch):
    parsed = {"simulations": [{"scenario": "heavy rain blocks routes", "likelihood": 30, "impact": 60, "affected_assumptions": []}]}
    metadata = PromptMetadata(prompt_version="v1", experiment_id="exp", model="m", fallback_model=None, cached=False, safety_blocked=False)
    ai_result = AIResult(task=AITask.simulation, metadata=metadata, raw_output="", parsed_output=parsed, usage={}, warnings=[])

    async def fake_run(req):
        return ai_result

    async def fake_create_simulation(session, project_id, scenario, likelihood=None, impact=None, affected_assumptions=None):
        return SimpleNamespace(id="s1", scenario=scenario)

    monkeypatch.setattr(ai_routes, "service", SimpleNamespace(run=fake_run))
    monkeypatch.setattr("app.crud.simulations.create_simulation", fake_create_simulation)

    req = AIRequest(task=AITask.simulation, input_text="idea", project_id="p1", dry_run=False)
    res = await ai_routes.generate_simulations(req, session=DummySession())
    assert "created" in res
    assert res["created"][0]["scenario"] == "heavy rain blocks routes"


@pytest.mark.asyncio
async def test_generate_simulations_background(monkeypatch):
    async def fake_run(req):
        return AIResult(task=AITask.simulation, metadata=PromptMetadata(prompt_version="v1", experiment_id="exp", model="m", fallback_model=None, cached=False, safety_blocked=False), raw_output="", parsed_output={"simulations": []}, usage={}, warnings=[])

    async def fake_create_run(session, project_id):
        return SimpleNamespace(id="r-bg")

    monkeypatch.setattr(ai_routes, "service", SimpleNamespace(run=fake_run))
    monkeypatch.setattr("app.crud.core.create_run", fake_create_run)

    req = AIRequest(task=AITask.simulation, input_text="idea", project_id="p1", dry_run=False)
    from fastapi import BackgroundTasks

    bg = BackgroundTasks()
    res = await ai_routes.generate_simulations(req, session=DummySession(), background=True, background_tasks=bg)
    assert res["status"] == "queued"
*** End Patch
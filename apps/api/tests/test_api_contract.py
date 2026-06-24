"""HTTP-level contract tests for public API endpoints."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient

from app.ai.schemas import AIResult, AITask, PromptMetadata
from app.api.routes import ai as ai_routes
from app.db import get_session
from app.main import app
from tests.conftest import DummyRedis


class DummySession:
    pass


async def _override_get_session():
    yield DummySession()


@pytest.fixture
def contract_client(monkeypatch):
    app.dependency_overrides[get_session] = _override_get_session
    monkeypatch.setattr("app.db.get_redis", lambda: DummyRedis())

    fake_user = SimpleNamespace(id="user-contract", email="test@example.com", is_active=True)

    from app.api.deps import get_current_active_user

    async def fake_current_user():
        return fake_user

    app.dependency_overrides[get_current_active_user] = fake_current_user

    async def fake_create_run(session, project_id):
        return SimpleNamespace(id="run-contract-1")

    monkeypatch.setattr("app.crud.core.create_run", fake_create_run)
    yield
    app.dependency_overrides.clear()


def _ai_result(task: AITask, parsed: dict) -> AIResult:
    return AIResult(
        task=task,
        metadata=PromptMetadata(
            prompt_version="v1",
            experiment_id="exp",
            model="test-model",
            fallback_model=None,
            cached=False,
            safety_blocked=False,
        ),
        raw_output="",
        parsed_output=parsed,
        usage={"total_tokens": 0},
        warnings=[],
    )


@pytest.mark.asyncio
async def test_ping_contract(contract_client):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/ping")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_contract(contract_client):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


@pytest.mark.asyncio
async def test_ai_preview_dry_run_contract(contract_client):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/ai/preview",
            json={"task": "decomposition", "input_text": "campus delivery", "dry_run": True},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["dry_run"] is True
    assert body["task"] == "decomposition"
    assert body["input_text"] == "campus delivery"


@pytest.mark.asyncio
async def test_ai_preview_validation_error(contract_client):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/ai/preview",
            json={"task": "decomposition", "input_text": "", "dry_run": True},
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_critiques_response_contract(contract_client, monkeypatch):
    parsed = {"critiques": [{"critique_text": "ops cost too high", "severity": 80}]}

    async def fake_run(req):
        return _ai_result(AITask.critique, parsed)

    async def fake_create_assumption(session, project_id, text):
        return SimpleNamespace(id="a-1")

    async def fake_create_critique(session, project_id, assumption_id, critique_text, severity=None):
        return SimpleNamespace(id="c-1", severity=severity)

    monkeypatch.setattr(ai_routes, "service", SimpleNamespace(run=fake_run))
    monkeypatch.setattr(ai_routes, "create_assumption", fake_create_assumption)
    monkeypatch.setattr(ai_routes, "create_critique", fake_create_critique)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/critiques",
            json={"task": "critique", "input_text": "free delivery for all", "project_id": "p1", "dry_run": False},
        )

    assert response.status_code == 200
    body = response.json()
    assert "created" in body
    assert body["created"][0]["id"] == "c-1"
    assert body["created"][0]["severity"] == 80
    assert body["raw"]["task"] == "critique"
    assert "parsed_output" in body["raw"]


@pytest.mark.asyncio
async def test_simulations_response_contract(contract_client, monkeypatch):
    parsed = {
        "simulations": [
            {"scenario": "driver shortage", "likelihood": 35, "impact": 65, "affected_assumptions": []}
        ]
    }

    async def fake_run(req):
        return _ai_result(AITask.simulation, parsed)

    async def fake_create_simulation(session, project_id, scenario, likelihood=None, impact=None, affected_assumptions=None):
        return SimpleNamespace(id="s-1", scenario=scenario)

    monkeypatch.setattr(ai_routes, "service", SimpleNamespace(run=fake_run))
    monkeypatch.setattr(ai_routes, "create_simulation", fake_create_simulation)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/simulations",
            json={"task": "simulation", "input_text": "campus delivery", "project_id": "p1", "dry_run": False},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["created"][0]["scenario"] == "driver shortage"
    assert body["raw"]["parsed_output"]["simulations"][0]["impact"] == 65


@pytest.mark.asyncio
async def test_reconstructions_response_contract(contract_client, monkeypatch):
    parsed = {
        "rebuilt_idea": "pilot in one dorm",
        "key_changes": ["narrow scope"],
        "risk_reductions": ["lower capex"],
    }

    async def fake_run(req):
        return _ai_result(AITask.reconstruction, parsed)

    async def fake_create_reconstruction(session, project_id, rebuilt_idea, key_changes=None, risk_reductions=None):
        return SimpleNamespace(id="rec-1", rebuilt_idea=rebuilt_idea)

    monkeypatch.setattr(ai_routes, "service", SimpleNamespace(run=fake_run))
    monkeypatch.setattr(ai_routes, "create_reconstruction", fake_create_reconstruction)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/reconstructions",
            json={"task": "reconstruction", "input_text": "campus delivery", "project_id": "p1", "dry_run": False},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "rec-1"
    assert body["rebuilt_idea"] == "pilot in one dorm"
    assert body["raw"]["task"] == "reconstruction"


@pytest.mark.asyncio
async def test_scores_response_contract(contract_client, monkeypatch):
    async def fake_compute(session, project_id):
        return [SimpleNamespace(id="score-1", assumption_id="a-1", risk_score=55)]

    monkeypatch.setattr(ai_routes, "compute_and_persist_scores", fake_compute)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/scores",
            json={"task": "assumptions", "input_text": "ignored", "project_id": "p1", "dry_run": False},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["created"][0]["risk_score"] == 55
    assert body["created"][0]["assumption_id"] == "a-1"


@pytest.mark.asyncio
async def test_debate_dry_run_contract(contract_client, monkeypatch):
    monkeypatch.setattr("app.ai.service.get_redis", lambda: SimpleNamespace(get=lambda *a, **k: None, set=lambda *a, **k: None))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/debate",
            json={"input_text": "launch with no ops team", "dry_run": True, "persona_keys": ["red_team"]},
        )

    assert response.status_code == 200
    body = response.json()
    assert "agents" in body
    assert "merged" in body
    assert body["agents"][0]["status"] == "planned"


@pytest.mark.asyncio
async def test_background_queue_contract(contract_client, monkeypatch):
    async def fake_run(req):
        return _ai_result(AITask.simulation, {"simulations": []})

    monkeypatch.setattr(ai_routes, "service", SimpleNamespace(run=fake_run))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/simulations?background=true",
            json={"task": "simulation", "input_text": "campus delivery", "project_id": "p1", "dry_run": False},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "queued"
    assert "run_id" in body

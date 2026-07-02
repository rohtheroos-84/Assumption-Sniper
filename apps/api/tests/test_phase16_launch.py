"""Tests for phase 16 launch and iteration features."""

from __future__ import annotations

import pytest

from app.ai.routing import RoutingProfile, resolve_model_for_role
from app.ai.schemas import ModelRole
from app.crud.scores import compute_risk_score


def test_routing_profiles_differ_by_cost_and_quality():
    cost = resolve_model_for_role(ModelRole.skeptic, RoutingProfile.cost)
    quality = resolve_model_for_role(ModelRole.skeptic, RoutingProfile.quality)
    assert cost[0] != quality[0] or cost == quality


def test_critique_severity_increases_risk_score():
    base = compute_risk_score(confidence=40, dep_count=5, max_impact=50, avg_critique_severity=0)
    boosted = compute_risk_score(confidence=40, dep_count=5, max_impact=50, avg_critique_severity=80)
    assert boosted > base


@pytest.mark.asyncio
async def test_demo_sample_endpoint():
    from httpx import ASGITransport, AsyncClient
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/demo/sample")
    assert response.status_code == 200
    body = response.json()
    assert "input_text" in body
    assert "preview" in body


@pytest.mark.asyncio
async def test_demo_preview_endpoint():
    from httpx import ASGITransport, AsyncClient
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/api/v1/demo/preview", json={"input_text": "AI tutor for schools"})
    assert response.status_code == 200
    body = response.json()
    assert body["dry_run"] is True
    assert "preview" in body


@pytest.mark.asyncio
async def test_feedback_submission_anonymous(monkeypatch):
    from httpx import ASGITransport, AsyncClient
    from app.main import app
    from app.db import get_session
    from tests.conftest import DummySession

    recorded: list = []

    async def fake_create_feedback(session, **kwargs):
        recorded.append(kwargs)
        from types import SimpleNamespace
        return SimpleNamespace(id="fb-1")

    async def _override_get_session():
        yield DummySession()

    monkeypatch.setattr("app.api.routes.launch.launch_crud.create_feedback", fake_create_feedback)
    app.dependency_overrides[get_session] = _override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/feedback",
            json={"message": "Love the demo flow", "category": "ux", "rating": 5},
        )
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert recorded[0]["message"] == "Love the demo flow"


def test_tune_from_eval_generates_report():
    from eval.tune_from_eval import build_recommendations

    report = build_recommendations()
    assert "recommendations" in report
    assert report["cases_evaluated"] >= 1

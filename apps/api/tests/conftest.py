"""Shared pytest configuration and fixtures."""

from __future__ import annotations

import os

# Required before any app imports that call get_settings().
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
os.environ.setdefault("JWT_SECRET", "test-secret-for-pytest")

import pytest
from types import SimpleNamespace


class DummySession:
    pass


class DummyRedis:
    async def get(self, *args, **kwargs):
        return None

    async def set(self, *args, **kwargs):
        return None

    async def ping(self):
        return True

    async def incr(self, *args, **kwargs):
        return 1

    async def expire(self, *args, **kwargs):
        return True


class NoopSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


@pytest.fixture(autouse=True)
def mock_ai_route_db_sessions(monkeypatch, request):
    module_name = getattr(request.module, "__name__", "")
    if module_name.endswith("test_pipeline_orchestrator"):
        return
    monkeypatch.setattr("app.api.routes.ai.AsyncSessionLocal", lambda: NoopSession())


@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    monkeypatch.setattr("app.db.get_redis", lambda: DummyRedis())
    monkeypatch.setattr("app.ai.service.get_redis", lambda: DummyRedis())
    monkeypatch.setattr("app.core.middleware.get_redis", lambda: DummyRedis())


@pytest.fixture
def dummy_session():
    return DummySession()


@pytest.fixture
def dummy_redis():
    return DummyRedis()


@pytest.fixture
def fake_run_factory():
    """Build a fake service.run coroutine from a task -> parsed_output map."""

    def _factory(outputs: dict):
        from app.ai.schemas import AIResult, PromptMetadata

        metadata = PromptMetadata(
            prompt_version="v1",
            experiment_id="exp",
            model="test-model",
            fallback_model=None,
            cached=False,
            safety_blocked=False,
        )

        async def fake_run(req):
            parsed = outputs.get(req.task.value, {})
            return AIResult(
                task=req.task,
                metadata=metadata,
                raw_output="",
                parsed_output=parsed,
                usage={"total_tokens": 0},
                warnings=[],
            )

        return fake_run

    return _factory


@pytest.fixture
def fake_create_run():
    async def _create_run(session, project_id):
        return SimpleNamespace(id="run-test-1")

    return _create_run

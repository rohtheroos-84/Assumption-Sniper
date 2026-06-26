"""Tests for phase 12 performance and reliability features."""

from __future__ import annotations

import json
import time
from types import SimpleNamespace

import pytest

from app.ai.batching import chunk_items, join_assumption_texts
from app.ai.circuit_breaker import CircuitOpenError, assert_circuit_closed, record_failure, record_success
from app.ai.schemas import AIRequest, AITask
from app.core.pagination import clamp_limit, serialize_page, PageResult
from app.core.queue import QueueTask, complete_pipeline_task, requeue_with_backoff, try_enqueue_pipeline
from app.pipeline import orchestrator as orch_module
from app.pipeline.orchestrator import PipelineOrchestrator


class InMemoryRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.lists: dict[str, list[str]] = {}
        self.counters: dict[str, int] = {}

    async def get(self, key):
        return self.values.get(key)

    async def set(self, key, value, ex=None):
        self.values[key] = value
        return True

    async def delete(self, *keys):
        for key in keys:
            self.values.pop(key, None)
            self.counters.pop(key, None)
        return len(keys)

    async def incr(self, key):
        self.counters[key] = self.counters.get(key, 0) + 1
        self.values[key] = str(self.counters[key])
        return self.counters[key]

    async def decr(self, key):
        self.counters[key] = self.counters.get(key, 0) - 1
        self.values[key] = str(self.counters[key])
        return self.counters[key]

    async def expire(self, key, seconds):
        return True

    async def llen(self, key):
        return len(self.lists.get(key, []))

    async def rpush(self, key, value):
        self.lists.setdefault(key, []).append(value)
        return len(self.lists[key])

    async def lpop(self, key):
        items = self.lists.get(key, [])
        if not items:
            return None
        return items.pop(0)


def test_clamp_limit_defaults_and_bounds():
    assert clamp_limit(None, default=50, maximum=200) == 50
    assert clamp_limit(500, default=50, maximum=200) == 200
    assert clamp_limit(0, default=50, maximum=200) == 1


def test_chunk_items_respects_batch_size():
    assert chunk_items([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
    assert chunk_items([], 3) == []


def test_join_assumption_texts_respects_max_chars():
    texts = ["a" * 100, "b" * 100, "c" * 100]
    joined = join_assumption_texts(texts, max_chars=150)
    assert joined.count("\n") <= 1
    assert len(joined) <= 150


def test_serialize_page_shape():
    page = PageResult(items=[SimpleNamespace(id="1")], next_cursor="1", has_more=True, limit=1)
    payload = serialize_page(page.items, page, lambda item: {"id": item.id})
    assert payload["items"] == [{"id": "1"}]
    assert payload["next_cursor"] == "1"
    assert payload["has_more"] is True
    assert payload["limit"] == 1


@pytest.mark.asyncio
async def test_queue_backpressure_blocks_when_full(monkeypatch):
    redis = InMemoryRedis()
    monkeypatch.setattr("app.core.queue.settings.max_queue_depth", 1)
    monkeypatch.setattr("app.core.queue.settings.max_concurrent_runs_per_user", 5)

    ok, _ = await try_enqueue_pipeline(redis, QueueTask(run_id="r1", project_id="p1", user_id="u1"))
    assert ok is True
    ok, reason = await try_enqueue_pipeline(redis, QueueTask(run_id="r2", project_id="p1", user_id="u1"))
    assert ok is False
    assert reason == "queue depth exceeded"


@pytest.mark.asyncio
async def test_queue_blocks_concurrent_runs_per_user(monkeypatch):
    redis = InMemoryRedis()
    monkeypatch.setattr("app.core.queue.settings.max_queue_depth", 50)
    monkeypatch.setattr("app.core.queue.settings.max_concurrent_runs_per_user", 1)

    ok, _ = await try_enqueue_pipeline(redis, QueueTask(run_id="r1", project_id="p1", user_id="u1"))
    assert ok is True
    ok, reason = await try_enqueue_pipeline(redis, QueueTask(run_id="r2", project_id="p1", user_id="u1"))
    assert ok is False
    assert reason == "too many concurrent runs"


@pytest.mark.asyncio
async def test_requeue_with_backoff_increments_attempt(monkeypatch):
    redis = InMemoryRedis()
    monkeypatch.setattr("app.core.queue.settings.max_queue_depth", 50)
    monkeypatch.setattr("app.core.queue.settings.max_concurrent_runs_per_user", 5)
    monkeypatch.setattr("app.core.queue.settings.queue_task_max_retries", 2)

    task = QueueTask(run_id="r1", project_id="p1", user_id="u1", attempt=0)
    await try_enqueue_pipeline(redis, task)
    await redis.lpop("queue:pipeline")
    await complete_pipeline_task(redis, "u1")

    ok = await requeue_with_backoff(redis, task)
    assert ok is True
    raw = await redis.lpop("queue:pipeline")
    payload = json.loads(raw)
    assert payload["attempt"] == 1


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failures(monkeypatch):
    redis = InMemoryRedis()
    monkeypatch.setattr("app.ai.circuit_breaker.settings.openrouter_circuit_failure_threshold", 2)
    monkeypatch.setattr("app.ai.circuit_breaker.settings.openrouter_circuit_cooldown_seconds", 60)

    await assert_circuit_closed(redis)
    await record_failure(redis)
    await record_failure(redis)

    with pytest.raises(CircuitOpenError):
        await assert_circuit_closed(redis)


@pytest.mark.asyncio
async def test_circuit_breaker_recovers_after_success():
    redis = InMemoryRedis()
    await redis.set("ai:circuit:openrouter", f"open:{time.time()}")
    await record_success(redis)
    await assert_circuit_closed(redis)


@pytest.mark.asyncio
async def test_orchestrator_retries_transient_stage_error(monkeypatch):
    monkeypatch.setattr("app.core.tracing.settings.tracing_enabled", False)
    events: list[str] = []
    attempts = {"n": 0}

    async def fake_update_run_status(session, run_id, status):
        return None

    async def fake_record_run_event(session, run_id, stage, event_type, payload_json):
        events.append(event_type)

    async def flaky_run(req: AIRequest):
        if req.task == AITask.decomposition and attempts["n"] == 0:
            attempts["n"] += 1
            raise RuntimeError("transient")
        from app.ai.schemas import AIResult, PromptMetadata

        return AIResult(
            task=req.task,
            metadata=PromptMetadata(
                prompt_version="v1",
                experiment_id="exp",
                model="test",
                fallback_model=None,
                cached=False,
                safety_blocked=False,
            ),
            parsed_output={},
            warnings=[],
        )

    class MockSession:
        async def get(self, model, obj_id):
            name = getattr(model, "__name__", str(model))
            if name == "Run":
                return SimpleNamespace(id=obj_id, status="running")
            if name == "Project":
                return SimpleNamespace(id=obj_id, input_text="idea")
            return None

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

    monkeypatch.setattr(orch_module, "AsyncSessionLocal", lambda: MockSession())
    monkeypatch.setattr(orch_module, "update_run_status", fake_update_run_status)
    monkeypatch.setattr(orch_module, "record_run_event", fake_record_run_event)
    monkeypatch.setattr(orch_module.service, "run", flaky_run)
    monkeypatch.setattr(orch_module.settings, "queue_task_max_retries", 2)

    orchestrator = PipelineOrchestrator()
    await orchestrator.run_pipeline("run-1", "proj-1")

    assert "stage_completed" in events
    assert events.count("stage_failed") == 0


@pytest.mark.asyncio
async def test_event_stream_serialization_helper():
    from app.api.routes.runs import _serialize_event

    event = SimpleNamespace(
        id="evt-1",
        stage="decomposition",
        event_type="stage_started",
        payload_json={"status": "running"},
        created_at=None,
    )
    payload = _serialize_event(event)
    assert payload["stage"] == "decomposition"
    assert payload["event_type"] == "stage_started"
    assert payload["type"] == "stage_started"

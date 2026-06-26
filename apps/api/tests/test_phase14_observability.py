"""Tests for phase 14 observability features."""

from __future__ import annotations

import json

import pytest

from app.core.logging import log_structured, request_id_var, run_id_var, trace_id_var
from app.core.metrics import metrics_enabled, record_ai_request, record_http_request, render_metrics
from app.core.tracing import PipelineTracer, Trace, load_trace


def test_render_metrics_exposes_prometheus_format():
    record_http_request("GET", "/api/v1/ping", 200, 0.01)
    body, content_type = render_metrics()
    assert content_type == "text/plain; version=0.0.4; charset=utf-8"
    assert b"http_requests_total" in body


def test_correlation_context_vars():
    request_id_var.set("req-1")
    trace_id_var.set("trace-1")
    run_id_var.set("run-1")
    assert request_id_var.get() == "req-1"
    assert trace_id_var.get() == "trace-1"
    assert run_id_var.get() == "run-1"


def test_trace_to_dict():
    trace = Trace(trace_id="t1", run_id="r1", spans=[])
    payload = trace.to_dict()
    assert payload["trace_id"] == "t1"
    assert payload["run_id"] == "r1"
    assert payload["spans"] == []


@pytest.mark.asyncio
async def test_pipeline_tracer_persists_spans(monkeypatch):
    stored: dict[str, str] = {}

    class MemoryRedis:
        async def set(self, key, value, ex=None):
            stored[key] = value
            return True

    monkeypatch.setattr("app.db.get_redis", lambda: MemoryRedis())
    monkeypatch.setattr("app.core.tracing.settings.tracing_enabled", True)

    tracer = PipelineTracer(run_id="run-1", trace_id="trace-1")
    async with tracer.span("decomposition"):
        pass
    await tracer.finalize(status="finished")

    assert "trace:run-1" in stored
    payload = json.loads(stored["trace:run-1"])
    assert payload["trace_id"] == "trace-1"
    assert len(payload["spans"]) == 1
    assert payload["spans"][0]["name"] == "decomposition"


@pytest.mark.asyncio
async def test_load_trace_reads_redis(monkeypatch):
    class MemoryRedis:
        async def get(self, key):
            if key == "trace:run-2":
                return json.dumps({"trace_id": "t2", "run_id": "run-2", "spans": []})
            return None

    monkeypatch.setattr("app.db.get_redis", lambda: MemoryRedis())
    trace = await load_trace("run-2")
    assert trace is not None
    assert trace["run_id"] == "run-2"


def test_record_ai_request_when_metrics_enabled(monkeypatch):
    monkeypatch.setattr("app.core.metrics.settings.metrics_enabled", True)
    record_ai_request(
        "decomposition",
        status="ok",
        duration_seconds=0.5,
        model="test-model",
        cost_usd=0.01,
        tokens=100,
    )
    body, _ = render_metrics()
    assert b"ai_requests_total" in body
    assert b"ai_cost_usd_total" in body


def test_metrics_disabled_skips_recording(monkeypatch):
    monkeypatch.setattr("app.core.metrics.settings.metrics_enabled", False)
    assert metrics_enabled() is False
    record_http_request("GET", "/ignored", 200, 0.01)

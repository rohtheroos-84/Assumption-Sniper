from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Iterator

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from app.core.config import get_settings

settings = get_settings()

HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
HTTP_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
AI_REQUESTS = Counter(
    "ai_requests_total",
    "Total AI task invocations",
    ["task", "status"],
)
AI_LATENCY = Histogram(
    "ai_request_duration_seconds",
    "AI task latency in seconds",
    ["task"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0),
)
AI_COST_USD = Counter(
    "ai_cost_usd_total",
    "Estimated AI spend in USD",
    ["task", "model"],
)
AI_TOKENS = Counter(
    "ai_tokens_total",
    "Total AI tokens consumed",
    ["task"],
)
PIPELINE_STAGE_LATENCY = Histogram(
    "pipeline_stage_duration_seconds",
    "Pipeline stage latency in seconds",
    ["stage"],
    buckets=(0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
)
ERRORS = Counter(
    "errors_total",
    "Total errors by component",
    ["component", "error_type"],
)
BUDGET_USD_HOURLY = Counter(
    "budget_usd_hourly_total",
    "Rolling hourly AI spend tracker for alerting",
    ["window"],
)


def metrics_enabled() -> bool:
    return settings.metrics_enabled


def record_http_request(method: str, path: str, status: int, duration_seconds: float) -> None:
    if not metrics_enabled():
        return
    HTTP_REQUESTS.labels(method=method, path=path, status=str(status)).inc()
    HTTP_LATENCY.labels(method=method, path=path).observe(duration_seconds)


def record_ai_request(
    task: str,
    *,
    status: str,
    duration_seconds: float,
    model: str,
    cost_usd: float,
    tokens: int,
) -> None:
    if not metrics_enabled():
        return
    AI_REQUESTS.labels(task=task, status=status).inc()
    AI_LATENCY.labels(task=task).observe(duration_seconds)
    AI_COST_USD.labels(task=task, model=model).inc(max(cost_usd, 0.0))
    AI_TOKENS.labels(task=task).inc(max(tokens, 0))
    if cost_usd > 0:
        BUDGET_USD_HOURLY.labels(window="current_hour").inc(cost_usd)


def record_pipeline_stage(stage: str, duration_seconds: float, *, status: str) -> None:
    if not metrics_enabled():
        return
    PIPELINE_STAGE_LATENCY.labels(stage=stage).observe(duration_seconds)
    if status != "ok":
        ERRORS.labels(component="pipeline", error_type=status).inc()


def record_error(component: str, error_type: str) -> None:
    if not metrics_enabled():
        return
    ERRORS.labels(component=component, error_type=error_type).inc()


@contextmanager
def observe_duration(histogram: Histogram, **labels: str) -> Iterator[None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        histogram.labels(**labels).observe(time.perf_counter() - start)


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST

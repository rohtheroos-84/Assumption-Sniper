"""Lightweight load test against in-process ASGI app; records p95 latencies."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
os.environ.setdefault("JWT_SECRET", "load-test-secret")


class LoadTestRedis:
    async def incr(self, *args, **kwargs):
        return 1

    async def expire(self, *args, **kwargs):
        return True

    async def ping(self):
        return True


_fake_redis = LoadTestRedis()
import app.db as db_module
import app.core.middleware as middleware_module

db_module.get_redis = lambda: _fake_redis
middleware_module.get_redis = lambda: _fake_redis

from httpx import ASGITransport, AsyncClient

from app.main import app

OUTPUT_PATH = Path(__file__).resolve().parents[3] / "docs" / "perf-baseline.json"
ENDPOINTS = (
    ("GET", "/api/v1/ping"),
    ("GET", "/api/v1/health"),
)


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = int(round((pct / 100.0) * (len(ordered) - 1)))
    return ordered[max(0, min(index, len(ordered) - 1))]


async def run_load(*, concurrency: int, requests_per_endpoint: int) -> dict:
    transport = ASGITransport(app=app)
    latencies: dict[str, list[float]] = {path: [] for _, path in ENDPOINTS}

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        sem = asyncio.Semaphore(concurrency)

        async def hit(method: str, path: str) -> None:
            async with sem:
                start = time.perf_counter()
                if method == "GET":
                    response = await client.get(path)
                else:
                    response = await client.post(path, json={})
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                latencies[path].append(elapsed_ms)
                response.raise_for_status()

        tasks = []
        for _ in range(requests_per_endpoint):
            for method, path in ENDPOINTS:
                tasks.append(asyncio.create_task(hit(method, path)))
        await asyncio.gather(*tasks)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "concurrency": concurrency,
        "requests_per_endpoint": requests_per_endpoint,
        "endpoints": {},
    }
    for _, path in ENDPOINTS:
        samples = latencies[path]
        summary["endpoints"][path] = {
            "count": len(samples),
            "mean_ms": round(statistics.mean(samples), 2) if samples else 0.0,
            "p50_ms": round(percentile(samples, 50), 2),
            "p95_ms": round(percentile(samples, 95), 2),
            "p99_ms": round(percentile(samples, 99), 2),
            "max_ms": round(max(samples), 2) if samples else 0.0,
        }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run API load test and record p95 latencies")
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--requests", type=int, default=50, help="Requests per endpoint")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()

    summary = asyncio.run(run_load(concurrency=args.concurrency, requests_per_endpoint=args.requests))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

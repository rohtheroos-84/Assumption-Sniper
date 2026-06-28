"""Post-deploy smoke tests for staging and production."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
os.environ.setdefault("JWT_SECRET", "smoke-test-secret")

from httpx import ASGITransport, AsyncClient

CHECKS = (
    ("GET", "/api/v1/ping", 200),
    ("GET", "/api/v1/health", 200),
    ("GET", "/api/v1/ready", 200),
    ("GET", "/api/v1/metrics", 200),
    ("GET", "/api/v1/ops/slo", 200),
)


class SmokeTestRedis:
    async def incr(self, *args, **kwargs):
        return 1

    async def expire(self, *args, **kwargs):
        return True

    async def ping(self):
        return True

    async def get(self, *args, **kwargs):
        return None

    async def set(self, *args, **kwargs):
        return True


async def run_smoke(base_url: str, *, in_process: bool = False) -> dict:
    results: list[dict] = []

    if in_process:
        import app.db as db_module
        import app.core.middleware as middleware_module
        from app.main import app

        fake = SmokeTestRedis()
        db_module.get_redis = lambda: fake
        middleware_module.get_redis = lambda: fake

        async def fake_check_db():
            return True

        db_module.check_db = fake_check_db
        transport = ASGITransport(app=app)
        client_ctx = AsyncClient(transport=transport, base_url="http://testserver")
    else:
        client_ctx = AsyncClient(base_url=base_url, timeout=30.0)

    async with client_ctx as client:
        for method, path, expected_status in CHECKS:
            start = asyncio.get_event_loop().time()
            try:
                if method == "GET":
                    response = await client.get(path)
                else:
                    response = await client.post(path, json={})
                ok = response.status_code == expected_status
                results.append(
                    {
                        "path": path,
                        "status": response.status_code,
                        "ok": ok,
                        "duration_ms": round((asyncio.get_event_loop().time() - start) * 1000, 2),
                    }
                )
            except Exception as exc:
                results.append({"path": path, "ok": False, "error": str(exc)})

    passed = all(item.get("ok") for item in results)
    return {"base_url": base_url, "passed": passed, "checks": results}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run deployment smoke tests")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--in-process", action="store_true", help="Run against in-process ASGI app")
    args = parser.parse_args()

    summary = asyncio.run(run_smoke(args.url, in_process=args.in_process))
    print(json.dumps(summary, indent=2))
    if not summary["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

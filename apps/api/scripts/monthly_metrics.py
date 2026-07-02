"""Aggregate success metrics for monthly iteration review."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/assumption_sniper")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
os.environ.setdefault("JWT_SECRET", "metrics-secret")

from sqlalchemy import func, select

from app.db import AsyncSessionLocal
from app.models import AnalyticsEvent, Feedback, Run, UsageRecord

OUTPUT = Path(__file__).resolve().parents[3] / "docs" / "metrics" / "monthly-snapshot.json"


async def collect() -> dict:
    async with AsyncSessionLocal() as session:
        runs = (await session.execute(select(func.count(Run.id)))).scalar() or 0
        feedback = (await session.execute(select(func.count(Feedback.id)))).scalar() or 0
        events = (await session.execute(select(func.count(AnalyticsEvent.id)))).scalar() or 0
        cost = (await session.execute(select(func.sum(UsageRecord.cost_usd)))).scalar() or 0
        tokens = (await session.execute(select(func.sum(UsageRecord.tokens)))).scalar() or 0

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runs_total": int(runs),
        "feedback_total": int(feedback),
        "analytics_events_total": int(events),
        "cost_usd_total": float(cost or 0),
        "tokens_total": int(tokens or 0),
        "kpis": {
            "weekly_active_runs_target": 50,
            "critique_relevance_min": 0.6,
            "monthly_retention_target_percent": 40,
        },
    }


def main() -> None:
    snapshot = asyncio.run(collect())
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()

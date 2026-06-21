"""Warm AI response cache for common evaluation prompts."""

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
os.environ.setdefault("JWT_SECRET", "warm-cache-secret")

from app.ai.schemas import AIRequest, AITask
from app.ai.service import build_ai_service
from app.core.config import get_settings

DATASET_PATH = Path(__file__).resolve().parents[1] / "eval" / "dataset.json"
WARM_TASKS = (AITask.decomposition, AITask.assumptions)


async def warm_prompts(*, execute: bool) -> dict[str, int]:
    settings = get_settings()
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    service = build_ai_service()
    warmed = 0
    skipped = 0

    for case in dataset.get("cases", []):
        input_text = case.get("input_text", "").strip()
        if not input_text:
            skipped += 1
            continue
        for task in WARM_TASKS:
            req = AIRequest(task=task, input_text=input_text, dry_run=False)
            if not execute:
                print(f"[dry-run] would warm {task.value} for {case.get('id', 'case')}")
                warmed += 1
                continue
            if settings.openrouter_api_key in {"change-me", "test-key"}:
                print("skipping live warm: OPENROUTER_API_KEY is not configured")
                return {"warmed": 0, "skipped": len(dataset.get("cases", []))}
            result = await service.run(req)
            print(f"warmed {task.value} for {case.get('id', 'case')} cached={result.metadata.cached}")
            warmed += 1

    return {"warmed": warmed, "skipped": skipped}


def main() -> None:
    parser = argparse.ArgumentParser(description="Warm AI cache for common prompts")
    parser.add_argument("--execute", action="store_true", help="Call OpenRouter and populate Redis cache")
    args = parser.parse_args()
    summary = asyncio.run(warm_prompts(execute=args.execute))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

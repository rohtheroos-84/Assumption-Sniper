from __future__ import annotations

import json
import time
from dataclasses import dataclass

from app.core.config import get_settings

settings = get_settings()


@dataclass(frozen=True)
class QueueTask:
    run_id: str
    project_id: str
    user_id: str | None = None
    attempt: int = 0


async def queue_depth(redis) -> int:
    return int(await redis.llen("queue:pipeline") or 0)


async def active_run_count(redis, user_id: str | None) -> int:
    if not user_id:
        return 0
    value = await redis.get(f"queue:active_runs:{user_id}")
    return int(value or 0)


async def try_enqueue_pipeline(redis, task: QueueTask) -> tuple[bool, str | None]:
    depth = await queue_depth(redis)
    if depth >= settings.max_queue_depth:
        return False, "queue depth exceeded"

    if task.user_id:
        active = await active_run_count(redis, task.user_id)
        if active >= settings.max_concurrent_runs_per_user:
            return False, "too many concurrent runs"

    payload = json.dumps(
        {
            "run_id": task.run_id,
            "project_id": task.project_id,
            "user_id": task.user_id,
            "attempt": task.attempt,
            "enqueued_at": time.time(),
        }
    )
    await redis.rpush("queue:pipeline", payload)
    if task.user_id:
        await redis.incr(f"queue:active_runs:{task.user_id}")
    return True, None


async def dequeue_pipeline(redis) -> QueueTask | None:
    raw = await redis.lpop("queue:pipeline")
    if not raw:
        return None
    payload = json.loads(raw)
    return QueueTask(
        run_id=payload["run_id"],
        project_id=payload["project_id"],
        user_id=payload.get("user_id"),
        attempt=int(payload.get("attempt") or 0),
    )


async def complete_pipeline_task(redis, user_id: str | None) -> None:
    if not user_id:
        return
    remaining = await redis.decr(f"queue:active_runs:{user_id}")
    if remaining < 0:
        await redis.set(f"queue:active_runs:{user_id}", 0)


async def requeue_with_backoff(redis, task: QueueTask) -> bool:
    if task.attempt >= settings.queue_task_max_retries:
        return False
    delayed = QueueTask(
        run_id=task.run_id,
        project_id=task.project_id,
        user_id=task.user_id,
        attempt=task.attempt + 1,
    )
    ok, _ = await try_enqueue_pipeline(redis, delayed)
    return ok

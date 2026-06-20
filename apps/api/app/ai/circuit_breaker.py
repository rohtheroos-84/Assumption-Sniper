from __future__ import annotations

import time

from app.core.config import get_settings

settings = get_settings()
CIRCUIT_KEY = "ai:circuit:openrouter"


class CircuitOpenError(RuntimeError):
    pass


async def assert_circuit_closed(redis) -> None:
    state = await redis.get(CIRCUIT_KEY)
    if not state:
        return
    if state.startswith("open:"):
        opened_at = float(state.split(":", 1)[1])
        if time.time() - opened_at < settings.openrouter_circuit_cooldown_seconds:
            raise CircuitOpenError("openrouter circuit breaker is open")
        await redis.set(CIRCUIT_KEY, "half_open")


async def record_success(redis) -> None:
    await redis.delete(CIRCUIT_KEY)
    await redis.delete(f"{CIRCUIT_KEY}:failures")


async def record_failure(redis) -> None:
    failures = await redis.incr(f"{CIRCUIT_KEY}:failures")
    if failures == 1:
        await redis.expire(f"{CIRCUIT_KEY}:failures", settings.openrouter_circuit_cooldown_seconds)
    if failures >= settings.openrouter_circuit_failure_threshold:
        await redis.set(CIRCUIT_KEY, f"open:{time.time()}", ex=settings.openrouter_circuit_cooldown_seconds)

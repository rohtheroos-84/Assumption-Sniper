from __future__ import annotations

import json
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass, field
from typing import Any, AsyncIterator

from app.core.config import get_settings
from app.core.logging import log_structured, run_id_var, trace_id_var

settings = get_settings()


@dataclass
class Span:
    name: str
    start_ms: float
    end_ms: float | None = None
    status: str = "running"
    attributes: dict[str, Any] = field(default_factory=dict)

    def finish(self, *, status: str = "ok", attributes: dict[str, Any] | None = None) -> None:
        self.end_ms = time.time() * 1000.0
        self.status = status
        if attributes:
            self.attributes.update(attributes)


@dataclass
class Trace:
    trace_id: str
    run_id: str
    spans: list[Span] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "run_id": self.run_id,
            "spans": [asdict(span) for span in self.spans],
        }


def new_trace_id() -> str:
    return str(uuid.uuid4())


class PipelineTracer:
    def __init__(self, run_id: str, trace_id: str | None = None) -> None:
        self.run_id = run_id
        self.trace_id = trace_id or new_trace_id()
        self.trace = Trace(trace_id=self.trace_id, run_id=run_id)

    @asynccontextmanager
    async def span(self, name: str, **attributes: Any) -> AsyncIterator[Span]:
        span = Span(name=name, start_ms=time.time() * 1000.0, attributes=dict(attributes))
        self.trace.spans.append(span)
        token_run = run_id_var.set(self.run_id)
        token_trace = trace_id_var.set(self.trace_id)
        log_structured(
            "pipeline span started",
            level="INFO",
            span=name,
            run_id=self.run_id,
            trace_id=self.trace_id,
            **attributes,
        )
        try:
            yield span
            span.finish(status="ok")
        except Exception as exc:
            span.finish(status="error", attributes={"error": str(exc)})
            raise
        finally:
            trace_id_var.reset(token_trace)
            run_id_var.reset(token_run)
            await self.persist()

    async def persist(self) -> None:
        if not settings.tracing_enabled:
            return
        from app.db import get_redis

        redis = get_redis()
        key = f"trace:{self.run_id}"
        await redis.set(key, json.dumps(self.trace.to_dict()), ex=settings.trace_ttl_seconds)

    async def finalize(self, *, status: str) -> None:
        log_structured(
            "pipeline trace finalized",
            level="INFO",
            run_id=self.run_id,
            trace_id=self.trace_id,
            status=status,
            span_count=len(self.trace.spans),
        )
        await self.persist()


async def load_trace(run_id: str) -> dict[str, Any] | None:
    from app.db import get_redis

    redis = get_redis()
    raw = await redis.get(f"trace:{run_id}")
    if not raw:
        return None
    return json.loads(raw)

from __future__ import annotations

import asyncio
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal
from app.ai.service import build_ai_service
from app.ai.schemas import AIRequest, AITask
from app.core.config import get_settings
from app.core.logging import log_structured
from app.core.metrics import record_error, record_pipeline_stage
from app.core.tracing import PipelineTracer, new_trace_id
from app.crud.core import record_run_event, update_run_status
from app.models import Project, Run

settings = get_settings()

service = build_ai_service()


class PipelineOrchestrator:
    STAGES = [
        AITask.decomposition,
        AITask.assumptions,
        AITask.critique,
        AITask.simulation,
        AITask.assumptions,
        AITask.reconstruction,
    ]

    async def run_pipeline(self, run_id: str, project_id: str, background: bool = True) -> None:
        trace_id = new_trace_id()
        tracer = PipelineTracer(run_id=run_id, trace_id=trace_id)

        async with AsyncSessionLocal() as session:
            await update_run_status(session, run_id, "running")
            await record_run_event(
                session,
                run_id,
                stage="orchestration",
                event_type="started",
                payload_json={"trace_id": trace_id},
            )

        log_structured("pipeline started", run_id=run_id, trace_id=trace_id, project_id=project_id)

        for stage in self.STAGES:
            async with AsyncSessionLocal() as session:
                r = await session.get(Run, run_id)
                if not r or r.status == "cancelled":
                    async with AsyncSessionLocal() as s2:
                        await record_run_event(s2, run_id, stage=stage.value, event_type="cancelled", payload_json={})
                        await update_run_status(s2, run_id, "cancelled")
                    await tracer.finalize(status="cancelled")
                    return

            stage_start = time.perf_counter()
            try:
                async with tracer.span(stage.value, project_id=project_id):
                    input_text = ""
                    async with AsyncSessionLocal() as s:
                        proj = await s.get(Project, project_id)
                        input_text = proj.input_text if proj else input_text
                    if not input_text:
                        input_text = " "

                    req = AIRequest(
                        task=stage,
                        input_text=input_text,
                        project_id=project_id,
                        run_id=run_id,
                        dry_run=False,
                    )

                    async with AsyncSessionLocal() as s2:
                        await record_run_event(
                            s2,
                            run_id,
                            stage=stage.value,
                            event_type="stage_started",
                            payload_json={"status": "running", "trace_id": trace_id},
                        )

                    result = None
                    for attempt in range(settings.queue_task_max_retries + 1):
                        try:
                            result = await service.run(req)
                            break
                        except Exception as exc:
                            if attempt >= settings.queue_task_max_retries:
                                raise
                            await asyncio.sleep(0.5 * (attempt + 1))
                    assert result is not None

                    async with AsyncSessionLocal() as s3:
                        await record_run_event(
                            s3,
                            run_id,
                            stage=stage.value,
                            event_type="stage_completed",
                            payload_json={"warnings": result.warnings, "trace_id": trace_id},
                        )

                record_pipeline_stage(stage.value, time.perf_counter() - stage_start, status="ok")
            except Exception as exc:
                record_pipeline_stage(stage.value, time.perf_counter() - stage_start, status="failed")
                record_error("pipeline", "stage_failed")
                async with AsyncSessionLocal() as s4:
                    await record_run_event(
                        s4,
                        run_id,
                        stage=stage.value,
                        event_type="stage_failed",
                        payload_json={"error": str(exc), "trace_id": trace_id},
                    )
                    await update_run_status(s4, run_id, "failed")
                await tracer.finalize(status="failed")
                return

        async with AsyncSessionLocal() as session:
            await update_run_status(session, run_id, "finished")
            await record_run_event(
                session,
                run_id,
                stage="orchestration",
                event_type="finished",
                payload_json={"trace_id": trace_id},
            )
        await tracer.finalize(status="finished")


orchestrator = PipelineOrchestrator()

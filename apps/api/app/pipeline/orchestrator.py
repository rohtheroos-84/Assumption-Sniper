from __future__ import annotations

import asyncio
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal
from app.ai.service import build_ai_service
from app.ai.schemas import AIRequest, AITask
from app.crud.core import record_run_event, update_run_status
from app.models import Project, Run

service = build_ai_service()


class PipelineOrchestrator:
    STAGES = [
        AITask.decomposition,
        AITask.assumptions,
        AITask.critique,
        AITask.simulation,
        AITask.assumptions,  # optional re-extraction after sims
        AITask.reconstruction,
    ]

    async def run_pipeline(self, run_id: str, project_id: str, background: bool = True) -> None:
        async with AsyncSessionLocal() as session:  # type: AsyncSession
            # mark running
            await update_run_status(session, run_id, "running")
            await record_run_event(session, run_id, stage="orchestration", event_type="started", payload_json={})

        # run stages sequentially
        for stage in self.STAGES:
            # check cancellation
            async with AsyncSessionLocal() as session:
                r = await session.get(Run, run_id)
                if not r or r.status == "cancelled":
                    async with AsyncSessionLocal() as s2:
                        await record_run_event(s2, run_id, stage=stage.value, event_type="cancelled", payload_json={})
                        await update_run_status(s2, run_id, "cancelled")
                    return

            try:
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

                evt_payload = {"stage": stage.value, "status": "running"}
                async with AsyncSessionLocal() as s2:
                    await record_run_event(s2, run_id, stage=stage.value, event_type="stage_started", payload_json=evt_payload)

                result = await service.run(req)

                async with AsyncSessionLocal() as s3:
                    await record_run_event(s3, run_id, stage=stage.value, event_type="stage_completed", payload_json={"warnings": result.warnings})
            except Exception as exc:
                async with AsyncSessionLocal() as s4:
                    await record_run_event(s4, run_id, stage=stage.value, event_type="stage_failed", payload_json={"error": str(exc)})
                    await update_run_status(s4, run_id, "failed")
                return

        # all stages done
        async with AsyncSessionLocal() as session:
            await update_run_status(session, run_id, "finished")
            await record_run_event(session, run_id, stage="orchestration", event_type="finished", payload_json={})


orchestrator = PipelineOrchestrator()

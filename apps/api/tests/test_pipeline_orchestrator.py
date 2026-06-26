"""Integration tests for pipeline stage orchestration."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.ai.schemas import AIRequest, AITask
from app.pipeline import orchestrator as orch_module
from app.pipeline.orchestrator import PipelineOrchestrator


class MockSession:
    def __init__(self, run_status: str = "running", project_input: str = "campus food delivery app"):
        self.run_status = run_status
        self.project_input = project_input

    async def get(self, model, obj_id):
        name = getattr(model, "__name__", str(model))
        if name == "Run":
            return SimpleNamespace(id=obj_id, status=self.run_status)
        if name == "Project":
            return SimpleNamespace(id=obj_id, input_text=self.project_input)
        return None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


@pytest.fixture
def pipeline_env(monkeypatch):
    monkeypatch.setattr("app.core.tracing.settings.tracing_enabled", False)
    events: list[dict] = []
    statuses: list[str] = []
    run_calls: list[AITask] = []

    async def fake_update_run_status(session, run_id, status):
        statuses.append(status)

    async def fake_record_run_event(session, run_id, stage, event_type, payload_json):
        events.append({"run_id": run_id, "stage": stage, "event_type": event_type, "payload": payload_json})

    async def fake_run(req: AIRequest):
        run_calls.append(req.task)
        from app.ai.schemas import AIResult, PromptMetadata

        return AIResult(
            task=req.task,
            metadata=PromptMetadata(
                prompt_version="v1",
                experiment_id="exp",
                model="test",
                fallback_model=None,
                cached=False,
                safety_blocked=False,
            ),
            parsed_output={},
            warnings=[],
        )

    monkeypatch.setattr(orch_module, "AsyncSessionLocal", lambda: MockSession())
    monkeypatch.setattr(orch_module, "update_run_status", fake_update_run_status)
    monkeypatch.setattr(orch_module, "record_run_event", fake_record_run_event)
    monkeypatch.setattr(orch_module.service, "run", fake_run)

    return {"events": events, "statuses": statuses, "run_calls": run_calls}


@pytest.mark.asyncio
async def test_pipeline_runs_all_stages_in_order(pipeline_env):
    orchestrator = PipelineOrchestrator()
    await orchestrator.run_pipeline("run-1", "proj-1")

    assert pipeline_env["statuses"][-1] == "finished"
    assert pipeline_env["run_calls"] == PipelineOrchestrator.STAGES

    started = [e for e in pipeline_env["events"] if e["event_type"] == "stage_started"]
    completed = [e for e in pipeline_env["events"] if e["event_type"] == "stage_completed"]
    assert len(started) == len(PipelineOrchestrator.STAGES)
    assert len(completed) == len(PipelineOrchestrator.STAGES)
    assert started[0]["stage"] == AITask.decomposition.value
    assert started[-1]["stage"] == AITask.reconstruction.value


@pytest.mark.asyncio
async def test_pipeline_stops_when_run_cancelled(monkeypatch, pipeline_env):
    cancel_after = 2
    stage_count = {"n": 0}

    async def fake_run(req: AIRequest):
        pipeline_env["run_calls"].append(req.task)
        stage_count["n"] += 1
        from app.ai.schemas import AIResult, PromptMetadata

        return AIResult(
            task=req.task,
            metadata=PromptMetadata(
                prompt_version="v1",
                experiment_id="exp",
                model="test",
                fallback_model=None,
                cached=False,
                safety_blocked=False,
            ),
            parsed_output={},
            warnings=[],
        )

    class CancellingSession(MockSession):
        async def get(self, model, obj_id):
            name = getattr(model, "__name__", str(model))
            if name == "Run" and stage_count["n"] >= cancel_after:
                return SimpleNamespace(id=obj_id, status="cancelled")
            return await super().get(model, obj_id)

    monkeypatch.setattr(orch_module, "AsyncSessionLocal", lambda: CancellingSession())
    monkeypatch.setattr(orch_module.service, "run", fake_run)

    orchestrator = PipelineOrchestrator()
    await orchestrator.run_pipeline("run-1", "proj-1")

    assert pipeline_env["statuses"][-1] == "cancelled"
    assert len(pipeline_env["run_calls"]) == cancel_after
    cancelled_events = [e for e in pipeline_env["events"] if e["event_type"] == "cancelled"]
    assert cancelled_events


@pytest.mark.asyncio
async def test_pipeline_marks_failed_on_stage_error(monkeypatch, pipeline_env):
    call_count = {"n": 0}

    async def failing_run(req: AIRequest):
        call_count["n"] += 1
        if req.task == AITask.simulation:
            raise RuntimeError("simulation model timeout")
        pipeline_env["run_calls"].append(req.task)
        from app.ai.schemas import AIResult, PromptMetadata

        return AIResult(
            task=req.task,
            metadata=PromptMetadata(
                prompt_version="v1",
                experiment_id="exp",
                model="test",
                fallback_model=None,
                cached=False,
                safety_blocked=False,
            ),
            parsed_output={},
            warnings=[],
        )

    monkeypatch.setattr(orch_module.service, "run", failing_run)

    orchestrator = PipelineOrchestrator()
    await orchestrator.run_pipeline("run-1", "proj-1")

    assert pipeline_env["statuses"][-1] == "failed"
    failed_events = [e for e in pipeline_env["events"] if e["event_type"] == "stage_failed"]
    assert len(failed_events) == 1
    assert failed_events[0]["stage"] == AITask.simulation.value
    assert "timeout" in failed_events[0]["payload"]["error"]


@pytest.mark.asyncio
async def test_pipeline_uses_project_input_text(monkeypatch, pipeline_env):
    captured: list[str] = []

    async def capture_run(req: AIRequest):
        captured.append(req.input_text)
        pipeline_env["run_calls"].append(req.task)
        from app.ai.schemas import AIResult, PromptMetadata

        return AIResult(
            task=req.task,
            metadata=PromptMetadata(
                prompt_version="v1",
                experiment_id="exp",
                model="test",
                fallback_model=None,
                cached=False,
                safety_blocked=False,
            ),
            parsed_output={},
            warnings=[],
        )

    monkeypatch.setattr(
        orch_module,
        "AsyncSessionLocal",
        lambda: MockSession(project_input="AI tutor for high school math"),
    )
    monkeypatch.setattr(orch_module.service, "run", capture_run)

    orchestrator = PipelineOrchestrator()
    await orchestrator.run_pipeline("run-1", "proj-1")

    assert all(text == "AI tutor for high school math" for text in captured)

from __future__ import annotations

import asyncio
import json
import time
from types import SimpleNamespace

import pytest

from app.ai.schemas import DebateRequest
from app.ai.service import AIService


class DummyRedis:
    async def get(self, *args, **kwargs):
        return None

    async def set(self, *args, **kwargs):
        return None


class FakeClient:
    async def chat_completion(self, *, model, system, user, temperature, max_tokens, seed=None, response_format=None):
        await asyncio.sleep(0.1)
        lowered = system.lower()
        if "red team reviewer" in lowered:
            critiques = {
                "critiques": [
                    {
                        "critique_text": "this will fail in production",
                        "assumption_id": "a-1",
                        "severity": 85,
                        "rationale": "hidden dependency risk",
                    }
                ]
            }
        elif "operations-minded reviewer" in lowered:
            critiques = {
                "critiques": [
                    {
                        "critique_text": "this will fail in production",
                        "assumption_id": "a-1",
                        "severity": 70,
                        "rationale": "ops readiness gap",
                    },
                    {
                        "critique_text": "monitoring is underspecified",
                        "assumption_id": "a-2",
                        "severity": 55,
                        "rationale": "no alerting plan",
                    },
                ]
            }
        else:
            critiques = {"critiques": []}

        return {
            "choices": [{"message": {"content": json.dumps(critiques)}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }

    @staticmethod
    def extract_text(result):
        choices = result.get("choices") or []
        if not choices:
            return ""
        return choices[0].get("message", {}).get("content", "")

    @staticmethod
    def extract_usage(result):
        usage = result.get("usage") or {}
        return {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }


@pytest.mark.asyncio
async def test_debate_runs_in_parallel_and_deduplicates(monkeypatch):
    monkeypatch.setattr("app.ai.service.get_redis", lambda: DummyRedis())
    service = AIService(client=FakeClient())

    request = DebateRequest(
        input_text="launch a new AI product with no ops staff",
        dry_run=False,
        persona_keys=["red_team", "operator"],
        max_agents=2,
        timeout_seconds=5,
    )

    started = time.perf_counter()
    result = await service.debate(request)
    duration = time.perf_counter() - started

    assert duration < 0.18
    assert len(result.agents) == 2
    assert {agent.status for agent in result.agents} == {"completed"}
    assert len(result.merged) == 2

    merged_texts = [item.critique_text for item in result.merged]
    assert "this will fail in production" in merged_texts
    duplicate = next(item for item in result.merged if item.critique_text == "this will fail in production")
    assert set(duplicate.sources) == {"red_team", "operator"}
    assert duplicate.severity == 85

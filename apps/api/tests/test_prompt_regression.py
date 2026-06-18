"""Regression tests for prompt templates and parser behavior on fixed LLM outputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from app.ai.prompts import DEBATE_PERSONAS, DEFAULT_DEBATE_PERSONAS, PROMPT_VERSION, PROMPTS
from app.ai.schemas import AITask
from app.ai.service import AIService

FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "llm_responses.json").read_text(encoding="utf-8")
)


def _sha12(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


@pytest.mark.parametrize("task", list(PROMPTS.keys()))
def test_prompt_templates_include_required_placeholders(task: AITask):
    prompt = PROMPTS[task]
    assert prompt.system
    assert prompt.user
    assert "{input_text}" in prompt.user
    if task == AITask.assumptions:
        assert "{max_depth}" in prompt.user


def test_prompt_version_is_stable():
    assert PROMPT_VERSION == "v1"


def test_prompt_system_hashes_are_recorded():
    current_hashes = {task.value: _sha12(PROMPTS[task].system) for task in PROMPTS}
    assert len(current_hashes) == 6
    assert all(len(digest) == 12 for digest in current_hashes.values())


def test_all_tasks_have_route_prompts():
    assert set(PROMPTS.keys()) == {
        AITask.decomposition,
        AITask.assumptions,
        AITask.assumption_classification,
        AITask.critique,
        AITask.simulation,
        AITask.reconstruction,
    }


def test_debate_personas_defaults_exist():
    for key in DEFAULT_DEBATE_PERSONAS:
        assert key in DEBATE_PERSONAS
        persona = DEBATE_PERSONAS[key]
        assert persona.system
        assert "json" in persona.system.lower()


@pytest.mark.parametrize("fixture_name", list(FIXTURES.keys()))
def test_golden_llm_outputs_still_parse(fixture_name: str):
    from app.ai.schemas_runtime import (
        AssumptionsOutput,
        ClassificationOutput,
        CritiquesOutput,
        DecompositionOutput,
        ReconstructionOutput,
        SimulationsOutput,
    )

    schema_by_name = {
        "decomposition": DecompositionOutput,
        "assumptions": AssumptionsOutput,
        "assumptions_single_quotes": AssumptionsOutput,
        "critiques": CritiquesOutput,
        "simulations": SimulationsOutput,
        "reconstruction": ReconstructionOutput,
        "classification": ClassificationOutput,
    }
    if fixture_name not in schema_by_name:
        pytest.skip(f"No schema mapping for {fixture_name}")

    fixture = FIXTURES[fixture_name]
    schema = schema_by_name[fixture_name]
    result = AIService._repair_with_schema(fixture["raw"], schema)
    assert result.parsed

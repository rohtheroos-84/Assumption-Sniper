from __future__ import annotations

from dataclasses import dataclass

from app.ai.schemas import AITask, ModelRole

PROMPT_VERSION = "v1"


@dataclass(frozen=True)
class PromptTemplate:
    role: ModelRole
    system: str
    user: str


PROMPTS: dict[AITask, PromptTemplate] = {
    AITask.decomposition: PromptTemplate(
        role=ModelRole.decomposition,
        system=(
            "you are an idea decomposition engine. break the input into targets, goals, "
            "dependencies, assumptions, and operational requirements. return strict json only."
        ),
        user="analyze this idea:\n\n{input_text}",
    ),
    AITask.assumptions: PromptTemplate(
        role=ModelRole.extraction,
        system=(
            "you are an assumption extraction engine. recursively identify hidden assumptions, "
            "parent-child chains, and categories. return strict json only."
        ),
        user="extract assumptions from this idea:\n\n{input_text}\n\nmax_depth={max_depth}",
    ),
    AITask.critique: PromptTemplate(
        role=ModelRole.skeptic,
        system=(
            "you are a hostile skeptic. attack the input, expose weak logic, unrealistic expectations, "
            "and operational risks. return strict json only."
        ),
        user="critique this idea:\n\n{input_text}",
    ),
    AITask.simulation: PromptTemplate(
        role=ModelRole.simulator,
        system=(
            "you are an edge-case simulator. generate realistic failure scenarios, likelihood, and impact. "
            "return strict json only."
        ),
        user="simulate failure scenarios for this idea:\n\n{input_text}",
    ),
    AITask.reconstruction: PromptTemplate(
        role=ModelRole.reconstruction,
        system=(
            "you are a reconstruction engine. improve the idea by narrowing scope, reducing risk, and "
            "increasing feasibility. return strict json only."
        ),
        user="rebuild this idea into a stronger version:\n\n{input_text}",
    ),
}

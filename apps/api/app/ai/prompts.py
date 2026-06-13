from __future__ import annotations

from dataclasses import dataclass

from app.ai.schemas import AITask, ModelRole

PROMPT_VERSION = "v1"


@dataclass(frozen=True)
class PromptTemplate:
    role: ModelRole
    system: str
    user: str


@dataclass(frozen=True)
class DebatePersona:
    key: str
    name: str
    focus: str
    system: str
    temperature: float = 0.5
    timeout_seconds: float = 12.0


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
    AITask.assumption_classification: PromptTemplate(
        role=ModelRole.classifier,
        system=(
            "you are an assumption classifier. given a list of short assumption statements, "
            "assign each a single category label from: product, user, market, ops, legal, finance, tech, other. "
            "return strict json mapping each assumption to a category."
        ),
        user="classify these assumptions (json array of strings):\n\n{input_text}",
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

DEBATE_PERSONAS: dict[str, DebatePersona] = {
    "red_team": DebatePersona(
        key="red_team",
        name="Red Team",
        focus="attack hidden assumptions and failure modes",
        system=(
            "you are the red team reviewer. challenge hidden assumptions, expose brittle logic, "
            "and prioritize concrete counterexamples. return strict json only."
        ),
        temperature=0.5,
        timeout_seconds=10.0,
    ),
    "operator": DebatePersona(
        key="operator",
        name="Operator",
        focus="deployment, maintainability, and observability",
        system=(
            "you are an operations-minded reviewer. focus on deployability, maintainability, cost, "
            "alerting, and incident risk. return strict json only."
        ),
        temperature=0.35,
        timeout_seconds=10.0,
    ),
    "customer": DebatePersona(
        key="customer",
        name="Customer Advocate",
        focus="user value, adoption risk, and product fit",
        system=(
            "you are a customer advocate. challenge unclear value, weak differentiation, and adoption risk. "
            "return strict json only."
        ),
        temperature=0.45,
        timeout_seconds=10.0,
    ),
    "adversary": DebatePersona(
        key="adversary",
        name="Adversary",
        focus="abuse cases, edge cases, and adversarial behavior",
        system=(
            "you are an adversarial reviewer. look for abuse cases, bad inputs, misleading claims, and edge cases. "
            "return strict json only."
        ),
        temperature=0.55,
        timeout_seconds=10.0,
    ),
}

DEFAULT_DEBATE_PERSONAS = ["red_team", "operator", "customer"]

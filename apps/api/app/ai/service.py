from __future__ import annotations

import asyncio
import hashlib
import json
import re
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Type

from pydantic import BaseModel, ValidationError

from app.ai.client import OpenRouterClient
from app.ai.routing import resolve_model_for_role
from app.ai.prompts import DEFAULT_DEBATE_PERSONAS, DEBATE_PERSONAS, PROMPT_VERSION, PROMPTS
from app.ai.schemas import AIRequest, AIResult, AITask, DebateRequest, ModelRole, PromptMetadata
from app.ai.schemas_runtime import (
    AssumptionsOutput,
    ClassificationOutput,
    CritiquesOutput,
    DebateAgentResult,
    DebateMergedCritique,
    DebateOutput,
    DecompositionOutput,
    ReconstructionOutput,
    SimulationsOutput,
    ValidationRepairResult,
)
from app.crud.core import record_run_event, record_run_usage
from app.db import AsyncSessionLocal
from app.core.config import get_settings
from app.core.metrics import record_ai_request, record_error
from app.core.output_filter import filter_output_text, filter_parsed_output
from app.core.safety import scan_prompt_injection
from app.db import get_redis

settings = get_settings()


@dataclass(frozen=True)
class RouteConfig:
    primary_model: str
    fallback_model: str
    temperature: float
    max_tokens: int


ROUTE_CONFIGS: dict[ModelRole, RouteConfig] = {
    ModelRole.decomposition: RouteConfig(settings.openrouter_fast_model, settings.openrouter_fallback_model, 0.1, settings.openrouter_max_tokens),
    ModelRole.extraction: RouteConfig(settings.openrouter_fast_model, settings.openrouter_fallback_model, 0.1, settings.openrouter_max_tokens),
    ModelRole.classifier: RouteConfig(settings.openrouter_fast_model, settings.openrouter_fallback_model, 0.0, settings.openrouter_max_tokens),
    ModelRole.skeptic: RouteConfig(settings.openrouter_reasoning_model, settings.openrouter_fallback_model, 0.4, settings.openrouter_max_tokens),
    ModelRole.simulator: RouteConfig(settings.openrouter_reasoning_model, settings.openrouter_fallback_model, 0.4, settings.openrouter_max_tokens),
    ModelRole.reconstruction: RouteConfig(settings.openrouter_reasoning_model, settings.openrouter_fallback_model, 0.3, settings.openrouter_max_tokens),
}

TASK_MODELS: dict[str, tuple[ModelRole, Type[BaseModel]]] = {
    "decomposition": (ModelRole.decomposition, DecompositionOutput),
    "assumptions": (ModelRole.extraction, AssumptionsOutput),
    "assumption_classification": (ModelRole.classifier, ClassificationOutput),
    "critique": (ModelRole.skeptic, CritiquesOutput),
    "simulation": (ModelRole.simulator, SimulationsOutput),
    "reconstruction": (ModelRole.reconstruction, ReconstructionOutput),
}

SAFE_PATTERNS = []  # kept for backward-compatible tests; use scan_prompt_injection instead

MODEL_PRICING = {
    settings.openrouter_fast_model: Decimal("0.0005"),
    settings.openrouter_reasoning_model: Decimal("0.0015"),
    settings.openrouter_fallback_model: Decimal("0.0008"),
}


class AIService:
    def __init__(self, client: OpenRouterClient | None = None) -> None:
        self.client = client or OpenRouterClient()
        self.redis = get_redis()

    def _cache_key(self, req: AIRequest, model: str) -> str:
        payload = {
            "task": req.task.value,
            "input_text": req.input_text,
            "model": model,
            "max_depth": req.max_depth,
            "prompt_version": PROMPT_VERSION,
        }
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
        return f"ai:cache:{digest}"

    def _experiment_id(self, req: AIRequest, model: str) -> str:
        raw = f"{PROMPT_VERSION}:{req.task.value}:{model}:{req.input_text[:128]}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]

    def _safety_scan(self, text: str) -> list[str]:
        return scan_prompt_injection(text)

    def _render_prompt(self, req: AIRequest) -> tuple[ModelRole, str, str, RouteConfig]:
        role, _ = TASK_MODELS[req.task.value]
        prompt = PROMPTS[req.task]
        base_route = ROUTE_CONFIGS[role]
        primary, fallback = resolve_model_for_role(role, settings.routing_profile)
        route = RouteConfig(primary, fallback, base_route.temperature, base_route.max_tokens)
        system = prompt.system
        user = prompt.user.format(input_text=req.input_text, max_depth=req.max_depth)
        return role, system, user, route

    @staticmethod
    def _normalize_critique_key(critique_text: str, assumption_id: str | None = None) -> str:
        normalized = re.sub(r"\s+", " ", critique_text.lower()).strip()
        normalized = re.sub(r"[^a-z0-9\s]+", "", normalized)
        if assumption_id:
            return f"{assumption_id}:{normalized}"
        return normalized

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        fenced = re.search(r"```json\s*(.*?)```", text, re.S | re.I)
        candidate = fenced.group(1).strip() if fenced else text.strip()
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = candidate[start : end + 1]
        return json.loads(candidate)

    @staticmethod
    def _repair_with_schema(raw_text: str, schema: Type[BaseModel]) -> ValidationRepairResult:
        try:
            parsed = AIService._extract_json(raw_text)
            schema.model_validate(parsed)
            return ValidationRepairResult(parsed=parsed, repaired=False)
        except Exception:
            repaired_text = raw_text.replace("'", '"')
            parsed = AIService._extract_json(repaired_text)
            schema.model_validate(parsed)
            return ValidationRepairResult(parsed=parsed, repaired=True, warnings=["repaired_json"])

    async def run(self, req: AIRequest) -> AIResult:
        start = time.perf_counter()
        result_status = "ok"
        try:
            result = await self._run_impl(req)
            if result.metadata.safety_blocked:
                result_status = "blocked"
            return result
        except Exception:
            result_status = "error"
            record_error("ai", req.task.value)
            raise
        finally:
            record_ai_request(
                req.task.value,
                status=result_status,
                duration_seconds=time.perf_counter() - start,
                model=getattr(self, "_last_model", "unknown"),
                cost_usd=getattr(self, "_last_cost_usd", 0.0),
                tokens=getattr(self, "_last_tokens", 0),
            )

    async def _run_impl(self, req: AIRequest) -> AIResult:
        self._last_model = settings.openrouter_fast_model
        self._last_cost_usd = 0.0
        self._last_tokens = 0
        warnings = self._safety_scan(req.input_text)
        role, system, user, route = self._render_prompt(req)
        _, schema = TASK_MODELS[req.task.value]
        model = route.primary_model
        fallback_model = route.fallback_model
        cache_key = self._cache_key(req, model)
        experiment_id = self._experiment_id(req, model)
        metadata = PromptMetadata(
            prompt_version=PROMPT_VERSION,
            experiment_id=experiment_id,
            model=model,
            fallback_model=fallback_model,
            cached=False,
            safety_blocked=bool(warnings),
        )

        if warnings:
            self._last_model = model
            return AIResult(task=req.task, metadata=metadata, parsed_output={}, warnings=warnings)

        cached = await self.redis.get(cache_key)
        if cached:
            payload = json.loads(cached)
            metadata.cached = True
            usage = payload.get("usage", {})
            self._set_usage_metrics(model, usage)
            return AIResult(
                task=req.task,
                metadata=metadata,
                raw_output=payload.get("raw_output"),
                parsed_output=payload.get("parsed_output", {}),
                usage=payload.get("usage", {}),
                warnings=payload.get("warnings", []),
            )

        result = await self.client.chat_completion(
            model=model,
            system=system,
            user=user,
            temperature=route.temperature,
            max_tokens=route.max_tokens,
        )
        raw_output = self.client.extract_text(result)
        usage = self.client.extract_usage(result)
        raw_output, output_warnings = filter_output_text(raw_output)
        warnings.extend(output_warnings)

        try:
            validated = self._repair_with_schema(raw_output, schema)
            parsed_output = validated.parsed
            parsed_output, parsed_warnings = filter_parsed_output(parsed_output)
            warnings.extend(parsed_warnings)
            if validated.repaired:
                warnings.append("response_required_json_repair")
        except Exception:
            # fallback model once if the primary output is not usable
            fallback_result = await self.client.chat_completion(
                model=fallback_model,
                system=system,
                user=user,
                temperature=route.temperature,
                max_tokens=route.max_tokens,
            )
            raw_output = self.client.extract_text(fallback_result)
            usage = self.client.extract_usage(fallback_result)
            raw_output, output_warnings = filter_output_text(raw_output)
            warnings.extend(output_warnings)
            validated = self._repair_with_schema(raw_output, schema)
            parsed_output = validated.parsed
            parsed_output, parsed_warnings = filter_parsed_output(parsed_output)
            warnings.extend(parsed_warnings)
            warnings.append("used_fallback_model")
            if validated.repaired:
                warnings.append("response_required_json_repair")

        payload = {
            "raw_output": raw_output,
            "parsed_output": parsed_output,
            "usage": usage,
            "warnings": warnings,
        }
        await self.redis.set(cache_key, json.dumps(payload), ex=settings.ai_cache_ttl_seconds)

        if req.run_id:
            cost_per_token = MODEL_PRICING.get(model, Decimal("0.001"))
            token_total = int(usage.get("total_tokens") or 0)
            cost_usd = float(cost_per_token * Decimal(token_total))
            async with AsyncSessionLocal() as session:
                await record_run_usage(
                    session,
                    req.run_id,
                    model_profile=model,
                    token_total=token_total,
                    cost_usd=cost_usd,
                )
                await record_run_event(
                    session,
                    req.run_id,
                    stage=req.task.value,
                    event_type="ai_result",
                    payload_json={
                        "prompt_version": PROMPT_VERSION,
                        "experiment_id": experiment_id,
                        "model": model,
                        "fallback_model": fallback_model,
                        "cached": False,
                        "warnings": warnings,
                    },
                )
        self._set_usage_metrics(model, usage)
        return AIResult(task=req.task, metadata=metadata, raw_output=raw_output, parsed_output=parsed_output, usage=usage, warnings=warnings)

    def _set_usage_metrics(self, model: str, usage: dict[str, Any]) -> None:
        self._last_model = model
        token_total = int(usage.get("total_tokens") or 0)
        self._last_tokens = token_total
        cost_per_token = MODEL_PRICING.get(model, Decimal("0.001"))
        self._last_cost_usd = float(cost_per_token * Decimal(token_total))

    async def debate(self, req: DebateRequest) -> DebateOutput:
        warnings = self._safety_scan(req.input_text)
        if warnings:
            metadata = PromptMetadata(
                prompt_version=PROMPT_VERSION,
                experiment_id="blocked",
                model=settings.openrouter_fast_model,
                fallback_model=None,
                cached=False,
                safety_blocked=True,
            )
            return DebateOutput(metadata=metadata, agents=[], merged=[])

        selected_keys = req.persona_keys or DEFAULT_DEBATE_PERSONAS
        personas = [DEBATE_PERSONAS[key] for key in selected_keys if key in DEBATE_PERSONAS][: req.max_agents]
        if not personas:
            personas = [DEBATE_PERSONAS[key] for key in DEFAULT_DEBATE_PERSONAS[: req.max_agents]]

        base_prompt = PROMPTS[AITask.critique]
        base_role = base_prompt.role
        route = ROUTE_CONFIGS[base_role]
        metadata = PromptMetadata(
            prompt_version=PROMPT_VERSION,
            experiment_id=self._experiment_id(AIRequest(task=AITask.critique, input_text=req.input_text, dry_run=False), route.primary_model),
            model=route.primary_model,
            fallback_model=route.fallback_model,
            cached=False,
            safety_blocked=False,
        )

        if req.dry_run:
            return DebateOutput(
                metadata=metadata,
                agents=[
                    DebateAgentResult(
                        key=persona.key,
                        name=persona.name,
                        focus=persona.focus,
                        timeout_seconds=persona.timeout_seconds,
                        temperature=persona.temperature,
                        status="planned",
                    )
                    for persona in personas
                ],
                merged=[],
            )

        async def run_persona(persona: Any) -> DebateAgentResult:
            system = f"{base_prompt.system}\n\nPersona focus: {persona.focus}\nPersona name: {persona.name}\nPersona instructions: {persona.system}"
            user = base_prompt.user.format(input_text=req.input_text)
            request = {
                "model": route.primary_model,
                "system": system,
                "user": user,
                "temperature": persona.temperature,
                "max_tokens": route.max_tokens,
            }
            try:
                result = await asyncio.wait_for(
                    self.client.chat_completion(**request),
                    timeout=min(persona.timeout_seconds, req.timeout_seconds),
                )
                raw_output = self.client.extract_text(result)
                usage = self.client.extract_usage(result)
                validated = self._repair_with_schema(raw_output, CritiquesOutput)
                parsed = validated.parsed
                critiques = CritiquesOutput.model_validate(parsed).critiques
                warnings: list[str] = []
                if validated.repaired:
                    warnings.append("response_required_json_repair")
                if req.run_id:
                    cost_per_token = MODEL_PRICING.get(route.primary_model, Decimal("0.001"))
                    token_total = int(usage.get("total_tokens") or 0)
                    cost_usd = float(cost_per_token * Decimal(token_total))
                    async with AsyncSessionLocal() as session:
                        await record_run_usage(
                            session,
                            req.run_id,
                            model_profile=route.primary_model,
                            token_total=token_total,
                            cost_usd=cost_usd,
                        )
                return DebateAgentResult(
                    key=persona.key,
                    name=persona.name,
                    focus=persona.focus,
                    timeout_seconds=persona.timeout_seconds,
                    temperature=persona.temperature,
                    status="completed",
                    critiques=critiques,
                    warnings=warnings,
                )
            except Exception as exc:
                return DebateAgentResult(
                    key=persona.key,
                    name=persona.name,
                    focus=persona.focus,
                    timeout_seconds=persona.timeout_seconds,
                    temperature=persona.temperature,
                    status="failed",
                    critiques=[],
                    warnings=["debate_agent_failed"],
                    error=str(exc),
                )

        agent_results = await asyncio.gather(*(run_persona(persona) for persona in personas))
        merged_map: dict[str, DebateMergedCritique] = {}
        for agent in agent_results:
            for critique in agent.critiques:
                key = self._normalize_critique_key(critique.critique_text, critique.assumption_id)
                current = merged_map.get(key)
                if current is None:
                    merged_map[key] = DebateMergedCritique(
                        critique_text=critique.critique_text,
                        severity=critique.severity,
                        assumption_id=critique.assumption_id,
                        rationale=critique.rationale,
                        sources=[agent.key],
                        source_roles=[agent.name],
                    )
                    continue
                current.severity = max(current.severity, critique.severity)
                if critique.assumption_id and not current.assumption_id:
                    current.assumption_id = critique.assumption_id
                if critique.rationale and critique.rationale not in (current.rationale or ""):
                    current.rationale = f"{current.rationale}; {critique.rationale}" if current.rationale else critique.rationale
                if agent.key not in current.sources:
                    current.sources.append(agent.key)
                if agent.name not in current.source_roles:
                    current.source_roles.append(agent.name)

        merged = sorted(merged_map.values(), key=lambda item: (-item.severity, item.critique_text))

        if req.run_id:
            async with AsyncSessionLocal() as session:
                await record_run_event(
                    session,
                    req.run_id,
                    stage="debate",
                    event_type="debate_completed",
                    payload_json={
                        "agents": [agent.model_dump() for agent in agent_results],
                        "merged_count": len(merged),
                    },
                )

        return DebateOutput(metadata=metadata, agents=agent_results, merged=merged)


def build_ai_service() -> AIService:
    return AIService()

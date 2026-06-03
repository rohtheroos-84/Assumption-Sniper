from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Type

from pydantic import BaseModel, ValidationError

from app.ai.client import OpenRouterClient
from app.ai.prompts import PROMPT_VERSION, PROMPTS
from app.ai.schemas import AIRequest, AIResult, ModelRole, PromptMetadata
from app.ai.schemas_runtime import (
    AssumptionsOutput,
    CritiquesOutput,
    DecompositionOutput,
    ReconstructionOutput,
    SimulationsOutput,
    ValidationRepairResult,
)
from app.crud.core import record_run_event, record_run_usage
from app.db import AsyncSessionLocal
from app.core.config import get_settings
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
    ModelRole.skeptic: RouteConfig(settings.openrouter_reasoning_model, settings.openrouter_fallback_model, 0.4, settings.openrouter_max_tokens),
    ModelRole.simulator: RouteConfig(settings.openrouter_reasoning_model, settings.openrouter_fallback_model, 0.4, settings.openrouter_max_tokens),
    ModelRole.reconstruction: RouteConfig(settings.openrouter_reasoning_model, settings.openrouter_fallback_model, 0.3, settings.openrouter_max_tokens),
}

TASK_MODELS: dict[str, tuple[ModelRole, Type[BaseModel]]] = {
    "decomposition": (ModelRole.decomposition, DecompositionOutput),
    "assumptions": (ModelRole.extraction, AssumptionsOutput),
    "critique": (ModelRole.skeptic, CritiquesOutput),
    "simulation": (ModelRole.simulator, SimulationsOutput),
    "reconstruction": (ModelRole.reconstruction, ReconstructionOutput),
}

SAFE_PATTERNS = [
    re.compile(r"ignore\s+previous\s+instructions", re.I),
    re.compile(r"system\s*prompt", re.I),
    re.compile(r"<\s*script", re.I),
]

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
        warnings: list[str] = []
        lowered = text.lower()
        for pattern in SAFE_PATTERNS:
            if pattern.search(lowered):
                warnings.append(f"blocked pattern: {pattern.pattern}")
        return warnings

    def _render_prompt(self, req: AIRequest) -> tuple[ModelRole, str, str, RouteConfig]:
        role, _ = TASK_MODELS[req.task.value]
        prompt = PROMPTS[req.task]
        route = ROUTE_CONFIGS[role]
        system = prompt.system
        user = prompt.user.format(input_text=req.input_text, max_depth=req.max_depth)
        return role, system, user, route

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
            return AIResult(task=req.task, metadata=metadata, parsed_output={}, warnings=warnings)

        cached = await self.redis.get(cache_key)
        if cached:
            payload = json.loads(cached)
            metadata.cached = True
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

        try:
            validated = self._repair_with_schema(raw_output, schema)
            parsed_output = validated.parsed
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
            validated = self._repair_with_schema(raw_output, schema)
            parsed_output = validated.parsed
            warnings.append("used_fallback_model")
            if validated.repaired:
                warnings.append("response_required_json_repair")

        payload = {
            "raw_output": raw_output,
            "parsed_output": parsed_output,
            "usage": usage,
            "warnings": warnings,
        }
        await self.redis.set(cache_key, json.dumps(payload), ex=60 * 60 * 24 * 7)

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
        return AIResult(task=req.task, metadata=metadata, raw_output=raw_output, parsed_output=parsed_output, usage=usage, warnings=warnings)


def build_ai_service() -> AIService:
    return AIService()

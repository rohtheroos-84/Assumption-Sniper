from __future__ import annotations

import asyncio
import hashlib
import json
from typing import Any, Optional

import httpx

from app.ai.circuit_breaker import assert_circuit_closed, record_failure, record_success
from app.ai.prompts import PROMPT_VERSION
from app.core.config import get_settings
from app.db import get_redis

settings = get_settings()


class OpenRouterClient:
    def __init__(self) -> None:
        self.settings = settings
        self._client = httpx.AsyncClient(
            base_url=str(self.settings.openrouter_base_url),
            timeout=httpx.Timeout(self.settings.openrouter_timeout_seconds),
            headers={
                "Authorization": f"Bearer {self.settings.openrouter_api_key}",
                "Content-Type": "application/json",
                "X-Title": "Assumption Sniper",
            },
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def chat_completion(
        self,
        *,
        model: str,
        system: str,
        user: str,
        temperature: float,
        max_tokens: int,
        seed: Optional[int] = None,
        response_format: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        redis = get_redis()
        await assert_circuit_closed(redis)

        payload: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if seed is not None:
            payload["seed"] = seed
        if response_format is not None:
            payload["response_format"] = response_format

        last_error: Exception | None = None
        for attempt in range(self.settings.openrouter_max_retries + 1):
            try:
                response = await self._client.post("/chat/completions", json=payload)
                response.raise_for_status()
                await record_success(redis)
                return response.json()
            except Exception as exc:
                last_error = exc
                await record_failure(redis)
                if attempt >= self.settings.openrouter_max_retries:
                    raise
                await asyncio.sleep(0.5 * (attempt + 1))
        if last_error:
            raise last_error
        raise RuntimeError("openrouter request failed")

    @staticmethod
    def extract_text(result: dict[str, Any]) -> str:
        choices = result.get("choices") or []
        if not choices:
            return ""
        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(part.get("text", "") for part in content if isinstance(part, dict))
        return ""

    @staticmethod
    def extract_usage(result: dict[str, Any]) -> dict[str, Any]:
        usage = result.get("usage") or {}
        return {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }

    @staticmethod
    def prompt_fingerprint(model: str, system: str, user: str) -> str:
        digest = hashlib.sha256(f"{PROMPT_VERSION}|{model}|{system}|{user}".encode("utf-8")).hexdigest()
        return digest[:16]

from __future__ import annotations

import re
from typing import Any

from app.core.config import get_settings

settings = get_settings()

INJECTION_PATTERNS = [
    re.compile(r"ignore\s+previous\s+instructions", re.I),
    re.compile(r"disregard\s+(all\s+)?prior\s+instructions", re.I),
    re.compile(r"system\s*prompt", re.I),
    re.compile(r"you\s+are\s+now\s+", re.I),
    re.compile(r"<\s*script", re.I),
    re.compile(r"jailbreak", re.I),
    re.compile(r"do\s+anything\s+now", re.I),
    re.compile(r"<\s*iframe", re.I),
]

CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitize_text(text: str, *, max_length: int | None = None) -> str:
    if max_length is None:
        max_length = settings.max_input_text_length
    cleaned = CONTROL_CHAR_PATTERN.sub("", text or "")
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = cleaned.strip()
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    return cleaned


def scan_prompt_injection(text: str) -> list[str]:
    warnings: list[str] = []
    for pattern in INJECTION_PATTERNS:
        if pattern.search(text):
            warnings.append(f"blocked pattern: {pattern.pattern}")
    return warnings


def validate_user_input(text: str) -> tuple[str, list[str]]:
    sanitized = sanitize_text(text)
    warnings = scan_prompt_injection(sanitized)
    return sanitized, warnings

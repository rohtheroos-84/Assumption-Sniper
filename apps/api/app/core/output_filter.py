from __future__ import annotations

import re
from typing import Any

UNSAFE_OUTPUT_PATTERNS = [
    (re.compile(r"<\s*script[^>]*>.*?</script>", re.I | re.S), "[removed script]"),
    (re.compile(r"<\s*iframe[^>]*>.*?</iframe>", re.I | re.S), "[removed iframe]"),
    (re.compile(r"javascript\s*:", re.I), "[removed javascript]"),
    (re.compile(r"on\w+\s*=", re.I), "[removed event handler]"),
]

PII_PATTERNS = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[redacted-ssn]"),
    (re.compile(r"\b(?:\d[ -]*?){13,16}\b"), "[redacted-card]"),
]


def filter_output_text(text: str) -> tuple[str, list[str]]:
    warnings: list[str] = []
    filtered = text
    for pattern, replacement in UNSAFE_OUTPUT_PATTERNS:
        if pattern.search(filtered):
            warnings.append(f"filtered unsafe output: {pattern.pattern}")
            filtered = pattern.sub(replacement, filtered)
    for pattern, replacement in PII_PATTERNS:
        if pattern.search(filtered):
            warnings.append(f"redacted sensitive output: {pattern.pattern}")
            filtered = pattern.sub(replacement, filtered)
    return filtered, warnings


def filter_parsed_output(parsed: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []

    def walk(value: Any) -> Any:
        if isinstance(value, str):
            filtered, local_warnings = filter_output_text(value)
            warnings.extend(local_warnings)
            return filtered
        if isinstance(value, dict):
            return {key: walk(item) for key, item in value.items()}
        if isinstance(value, list):
            return [walk(item) for item in value]
        return value

    return walk(parsed), warnings

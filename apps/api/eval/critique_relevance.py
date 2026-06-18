"""Heuristic critique relevance scoring for evaluation runs."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DATASET_PATH = Path(__file__).parent / "dataset.json"


@dataclass(frozen=True)
class CritiqueRelevanceResult:
    case_id: str
    critique_text: str
    keyword_hits: int
    keyword_total: int
    relevance_score: float
    passed: bool


@dataclass(frozen=True)
class CaseEvalResult:
    case_id: str
    passed: bool
    average_relevance: float
    critique_results: list[CritiqueRelevanceResult]
    theme_coverage: float


def load_eval_dataset(path: Path | None = None) -> dict[str, Any]:
    target = path or DATASET_PATH
    return json.loads(target.read_text(encoding="utf-8"))


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def critique_keyword_relevance(
    critique_text: str, expected_keywords: list[str]
) -> tuple[int, int, float]:
    if not expected_keywords:
        return 0, 0, 0.0
    normalized = normalize_text(critique_text)
    hits = sum(1 for keyword in expected_keywords if normalize_text(keyword) in normalized)
    score = hits / len(expected_keywords)
    return hits, len(expected_keywords), score


def evaluate_critique(
    *,
    case_id: str,
    critique_text: str,
    expected_keywords: list[str],
    min_relevance: float,
) -> CritiqueRelevanceResult:
    hits, total, score = critique_keyword_relevance(critique_text, expected_keywords)
    return CritiqueRelevanceResult(
        case_id=case_id,
        critique_text=critique_text,
        keyword_hits=hits,
        keyword_total=total,
        relevance_score=score,
        passed=score >= min_relevance,
    )


def theme_coverage(case: dict[str, Any], critiques: list[dict[str, Any]]) -> float:
    themes = case.get("expected_themes") or []
    if not themes:
        return 1.0
    combined = " ".join(normalize_text(c.get("critique_text", "")) for c in critiques)
    covered = sum(
        1
        for theme in themes
        if any(word in combined for word in normalize_text(theme).split())
    )
    return covered / len(themes)


def evaluate_case(
    case: dict[str, Any],
    critiques: list[dict[str, Any]] | None = None,
    *,
    min_relevance: float = 0.2,
    min_average_relevance: float = 0.25,
    min_theme_coverage: float = 0.34,
) -> CaseEvalResult:
    case_id = case["id"]
    expected_keywords = case.get("expected_keywords") or []
    source_critiques = critiques if critiques is not None else case.get("sample_critiques") or []

    critique_results = [
        evaluate_critique(
            case_id=case_id,
            critique_text=item["critique_text"],
            expected_keywords=expected_keywords,
            min_relevance=min_relevance,
        )
        for item in source_critiques
    ]

    average_relevance = (
        sum(result.relevance_score for result in critique_results) / len(critique_results)
        if critique_results
        else 0.0
    )
    themes = theme_coverage(case, source_critiques)
    passed = (
        bool(critique_results)
        and average_relevance >= min_average_relevance
        and themes >= min_theme_coverage
        and all(result.passed for result in critique_results)
    )

    return CaseEvalResult(
        case_id=case_id,
        passed=passed,
        average_relevance=average_relevance,
        critique_results=critique_results,
        theme_coverage=themes,
    )


def evaluate_dataset(
    dataset: dict[str, Any] | None = None,
    *,
    min_relevance: float = 0.2,
    min_average_relevance: float = 0.25,
    min_theme_coverage: float = 0.34,
) -> list[CaseEvalResult]:
    payload = dataset or load_eval_dataset()
    return [
        evaluate_case(
            case,
            min_relevance=min_relevance,
            min_average_relevance=min_average_relevance,
            min_theme_coverage=min_theme_coverage,
        )
        for case in payload.get("cases", [])
    ]

"""Generate prompt and scoring tuning recommendations from eval dataset."""

from __future__ import annotations

import json
from pathlib import Path

from eval.critique_relevance import evaluate_dataset, load_eval_dataset

OUTPUT_PATH = Path(__file__).resolve().parent / "tuning_report.json"


def build_recommendations() -> dict:
    dataset = load_eval_dataset()
    results = evaluate_dataset(dataset, min_relevance=0.5)
    failed_cases = [r for r in results if not r.passed]
    recommendations: list[str] = []

    if failed_cases:
        recommendations.append(
            "Tighten critique prompt to require keyword-aligned failure modes for: "
            + ", ".join(c.case_id for c in failed_cases)
        )
        recommendations.append("Increase skeptic temperature slightly for under-performing cases.")
    else:
        recommendations.append("Critique relevance meets threshold; keep current prompt version.")

    recommendations.append("Use routing_profile=balanced for beta; switch to quality for paid tier.")
    recommendations.append("Risk scoring uses critique severity boost—re-run eval after prompt changes.")

    report = {
        "cases_evaluated": len(results),
        "cases_passed": sum(1 for r in results if r.passed),
        "average_relevance": round(sum(r.average_relevance for r in results) / max(len(results), 1), 3),
        "recommendations": recommendations,
        "failed_cases": [
            {"case_id": c.case_id, "average_relevance": c.average_relevance, "theme_coverage": c.theme_coverage}
            for c in failed_cases
        ],
    }
    return report


def main() -> None:
    report = build_recommendations()
    OUTPUT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

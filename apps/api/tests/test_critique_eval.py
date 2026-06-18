"""Automated evaluation tests for critique relevance."""

from __future__ import annotations

from eval.critique_relevance import (
    critique_keyword_relevance,
    evaluate_case,
    evaluate_dataset,
    load_eval_dataset,
)


def test_dataset_has_cases():
    dataset = load_eval_dataset()
    assert dataset["version"] == "1"
    assert len(dataset["cases"]) >= 3
    for case in dataset["cases"]:
        assert case["id"]
        assert case["input_text"]
        assert case["expected_keywords"]
        assert case["sample_critiques"]


def test_critique_keyword_relevance_scores_hits():
    hits, total, score = critique_keyword_relevance(
        "Campus delivery costs are underestimated without dedicated routing",
        ["driver", "cost", "margin", "delivery", "campus"],
    )
    assert hits >= 3
    assert total == 5
    assert score >= 0.6


def test_sample_critiques_meet_relevance_threshold():
    dataset = load_eval_dataset()
    results = evaluate_dataset(dataset)
    assert len(results) == len(dataset["cases"])
    assert all(result.passed for result in results), [r.case_id for r in results if not r.passed]


def test_weak_critiques_fail_eval():
    case = load_eval_dataset()["cases"][0]
    weak = [{"critique_text": "This idea is interesting and could work well", "severity": 10}]
    result = evaluate_case(case, critiques=weak, min_relevance=0.2, min_average_relevance=0.25)
    assert result.passed is False
    assert result.average_relevance < 0.25

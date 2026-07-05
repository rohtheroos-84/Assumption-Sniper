"""Tests for phase 17 production exit criteria."""

from __future__ import annotations

from app.ops.exit_criteria import (
    check_eval_metrics,
    check_latency_and_error_budget,
    run_all_checks,
)


def test_latency_baseline_meets_slo():
    result = check_latency_and_error_budget()
    assert result.passed, result.detail


def test_eval_dataset_meets_thresholds():
    result = check_eval_metrics()
    assert result.passed, result.detail


def test_all_exit_criteria_pass():
    results = run_all_checks()
    failures = [item for item in results if not item.passed]
    assert not failures, [(item.id, item.detail) for item in failures]

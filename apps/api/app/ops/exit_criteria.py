"""Production exit-criteria checks for v1 release gate."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from eval.critique_relevance import evaluate_dataset

REPO_ROOT = Path(__file__).resolve().parents[4]
PERF_BASELINE_PATH = REPO_ROOT / "docs" / "observability" / "perf-baseline.json"
EVAL_THRESHOLDS_PATH = REPO_ROOT / "docs" / "release" / "eval-thresholds.json"
SECURITY_REPORT_PATH = REPO_ROOT / "docs" / "security" / "review-report.md"
BACKUP_RECORD_PATH = REPO_ROOT / "docs" / "operations" / "backup-restore-test-record.json"
DRILL_LOG_PATH = REPO_ROOT / "docs" / "operations" / "drill-log.md"
RELEASE_NOTES_PATH = REPO_ROOT / "docs" / "release" / "v1.0.0.md"
SIGN_OFF_PATH = REPO_ROOT / "docs" / "release" / "sign-off.md"
REPORT_PATH = REPO_ROOT / "docs" / "release" / "exit-criteria-report.json"

P95_LATENCY_MS = 500
MAX_ERROR_RATE = 0.005

REQUIRED_DOCS = [
    "docs/index.md",
    "docs/project-complete.md",
    "docs/getting-started.md",
    "docs/architecture.md",
    "docs/security/permissions.md",
    "docs/security/review-report.md",
    "docs/observability/slo-definitions.md",
    "docs/observability/perf-baseline.json",
    "docs/observability/prometheus-alerts.yml",
    "docs/observability/grafana-dashboard.json",
    "docs/operations/backup-restore.md",
    "docs/operations/drill-log.md",
    "docs/operations/runbooks/pipeline-failures.md",
    "docs/operations/runbooks/high-error-rate.md",
    "docs/operations/runbooks/budget-burn.md",
    "docs/operations/runbooks/redis-db-outage.md",
    "docs/on-call/escalation.md",
    "docs/on-call/rotation.json",
    "docs/deploy/infrastructure.md",
    "docs/deploy/launch-checklist.md",
    "docs/deploy/rollback.md",
    "docs/beta/program.md",
    "docs/release/v1.0.0.md",
    "docs/release/sign-off.md",
]


@dataclass
class CriterionResult:
    id: str
    name: str
    passed: bool
    detail: str


def check_latency_and_error_budget() -> CriterionResult:
    if not PERF_BASELINE_PATH.is_file():
        return CriterionResult(
            id="latency_error_budget",
            name="p95 latency and error budgets meet targets",
            passed=False,
            detail=f"missing baseline: {PERF_BASELINE_PATH.relative_to(REPO_ROOT)}",
        )

    baseline = json.loads(PERF_BASELINE_PATH.read_text(encoding="utf-8"))
    endpoints = baseline.get("endpoints") or {}
    failures: list[str] = []
    for path, stats in endpoints.items():
        p95 = stats.get("p95_ms")
        if p95 is None:
            failures.append(f"{path}: no p95_ms")
        elif p95 > P95_LATENCY_MS:
            failures.append(f"{path}: p95 {p95}ms > {P95_LATENCY_MS}ms")

    error_rate = float(baseline.get("error_rate", 0.0))
    if error_rate > MAX_ERROR_RATE:
        failures.append(f"error_rate {error_rate:.4f} > {MAX_ERROR_RATE:.4f}")

    if failures:
        return CriterionResult(
            id="latency_error_budget",
            name="p95 latency and error budgets meet targets",
            passed=False,
            detail="; ".join(failures),
        )

    return CriterionResult(
        id="latency_error_budget",
        name="p95 latency and error budgets meet targets",
        passed=True,
        detail=f"all {len(endpoints)} endpoints under {P95_LATENCY_MS}ms p95; error_rate={error_rate:.4f}",
    )


def check_eval_metrics() -> CriterionResult:
    thresholds = json.loads(EVAL_THRESHOLDS_PATH.read_text(encoding="utf-8"))
    min_pass_rate = float(thresholds["min_pass_rate"])
    min_avg_relevance = float(thresholds["min_average_relevance"])
    min_theme_coverage = float(thresholds["min_theme_coverage"])

    results = evaluate_dataset(
        min_relevance=float(thresholds.get("min_relevance", 0.2)),
        min_average_relevance=min_avg_relevance,
        min_theme_coverage=min_theme_coverage,
    )
    if not results:
        return CriterionResult(
            id="eval_metrics",
            name="eval metrics meet quality thresholds",
            passed=False,
            detail="eval dataset has no cases",
        )

    passed_cases = sum(1 for item in results if item.passed)
    pass_rate = passed_cases / len(results)
    avg_relevance = sum(item.average_relevance for item in results) / len(results)
    avg_themes = sum(item.theme_coverage for item in results) / len(results)

    failures: list[str] = []
    if pass_rate < min_pass_rate:
        failures.append(f"pass_rate {pass_rate:.2f} < {min_pass_rate:.2f}")
    if avg_relevance < min_avg_relevance:
        failures.append(f"avg_relevance {avg_relevance:.2f} < {min_avg_relevance:.2f}")
    if avg_themes < min_theme_coverage:
        failures.append(f"avg_theme_coverage {avg_themes:.2f} < {min_theme_coverage:.2f}")

    if failures:
        return CriterionResult(
            id="eval_metrics",
            name="eval metrics meet quality thresholds",
            passed=False,
            detail="; ".join(failures),
        )

    return CriterionResult(
        id="eval_metrics",
        name="eval metrics meet quality thresholds",
        passed=True,
        detail=(
            f"{passed_cases}/{len(results)} cases passed; "
            f"avg_relevance={avg_relevance:.2f}; theme_coverage={avg_themes:.2f}"
        ),
    )


def check_security_review() -> CriterionResult:
    if not SECURITY_REPORT_PATH.is_file():
        return CriterionResult(
            id="security_review",
            name="security review passed with no critical findings",
            passed=False,
            detail="missing security review report",
        )

    text = SECURITY_REPORT_PATH.read_text(encoding="utf-8").lower()
    if "status: approved" not in text:
        return CriterionResult(
            id="security_review",
            name="security review passed with no critical findings",
            passed=False,
            detail="report missing approved status",
        )

    if "critical findings: 0" not in text:
        return CriterionResult(
            id="security_review",
            name="security review passed with no critical findings",
            passed=False,
            detail="report does not confirm zero critical findings",
        )

    return CriterionResult(
        id="security_review",
        name="security review passed with no critical findings",
        passed=True,
        detail="approved with zero critical findings (see docs/security/review-report.md)",
    )


def check_backup_restore() -> CriterionResult:
    if not BACKUP_RECORD_PATH.is_file():
        return CriterionResult(
            id="backup_restore",
            name="backup and restore tested end to end",
            passed=False,
            detail="missing backup-restore test record; run scripts/backup_restore_test.py",
        )

    record = json.loads(BACKUP_RECORD_PATH.read_text(encoding="utf-8"))
    if not record.get("passed"):
        return CriterionResult(
            id="backup_restore",
            name="backup and restore tested end to end",
            passed=False,
            detail=record.get("detail", "last backup-restore test failed"),
        )

    return CriterionResult(
        id="backup_restore",
        name="backup and restore tested end to end",
        passed=True,
        detail=f"last test at {record.get('tested_at', 'unknown')}",
    )


def check_incident_drills() -> CriterionResult:
    if not DRILL_LOG_PATH.is_file():
        return CriterionResult(
            id="incident_drills",
            name="incident response drills completed",
            passed=False,
            detail="missing drill log",
        )

    text = DRILL_LOG_PATH.read_text(encoding="utf-8")
    if "status: completed" not in text.lower():
        return CriterionResult(
            id="incident_drills",
            name="incident response drills completed",
            passed=False,
            detail="no completed drill entries in drill-log.md",
        )

    return CriterionResult(
        id="incident_drills",
        name="incident response drills completed",
        passed=True,
        detail="drill log contains completed incident response exercise",
    )


def check_docs_and_runbooks() -> CriterionResult:
    missing = [path for path in REQUIRED_DOCS if not (REPO_ROOT / path).is_file()]
    if missing:
        return CriterionResult(
            id="docs_runbooks",
            name="docs and runbooks complete",
            passed=False,
            detail=f"missing {len(missing)} files: {', '.join(missing[:5])}"
            + ("..." if len(missing) > 5 else ""),
        )

    return CriterionResult(
        id="docs_runbooks",
        name="docs and runbooks complete",
        passed=True,
        detail=f"all {len(REQUIRED_DOCS)} required documentation files present",
    )


def check_release_notes() -> CriterionResult:
    if not RELEASE_NOTES_PATH.is_file():
        return CriterionResult(
            id="release_notes",
            name="release notes prepared",
            passed=False,
            detail="missing docs/release/v1.0.0.md",
        )

    content = RELEASE_NOTES_PATH.read_text(encoding="utf-8").strip()
    if len(content) < 200:
        return CriterionResult(
            id="release_notes",
            name="release notes prepared",
            passed=False,
            detail="release notes file is too short",
        )

    return CriterionResult(
        id="release_notes",
        name="release notes prepared",
        passed=True,
        detail="docs/release/v1.0.0.md ready",
    )


def check_owner_sign_off() -> CriterionResult:
    if not SIGN_OFF_PATH.is_file():
        return CriterionResult(
            id="owner_sign_off",
            name="owner sign-off for v1 production release",
            passed=False,
            detail="missing sign-off document",
        )

    text = SIGN_OFF_PATH.read_text(encoding="utf-8").lower()
    if "release status: approved" not in text:
        return CriterionResult(
            id="owner_sign_off",
            name="owner sign-off for v1 production release",
            passed=False,
            detail="sign-off document not marked approved",
        )

    return CriterionResult(
        id="owner_sign_off",
        name="owner sign-off for v1 production release",
        passed=True,
        detail="v1 production release approved in docs/release/sign-off.md",
    )


def run_all_checks() -> list[CriterionResult]:
    return [
        check_latency_and_error_budget(),
        check_eval_metrics(),
        check_security_review(),
        check_backup_restore(),
        check_incident_drills(),
        check_docs_and_runbooks(),
        check_release_notes(),
        check_owner_sign_off(),
    ]


def build_report(*, write: bool = True) -> dict[str, Any]:
    results = run_all_checks()
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "version": "v1.0.0",
        "passed": all(item.passed for item in results),
        "criteria": [asdict(item) for item in results],
    }
    if write:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report

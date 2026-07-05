"""Verify phase 17 production exit criteria and write the gate report."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ops.exit_criteria import build_report  # noqa: E402


def main() -> int:
    report = build_report(write=True)
    for item in report["criteria"]:
        status = "PASS" if item["passed"] else "FAIL"
        print(f"[{status}] {item['name']}: {item['detail']}")

    print(f"\nReport: docs/release/exit-criteria-report.json")
    print(f"Overall: {'PASS' if report['passed'] else 'FAIL'}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

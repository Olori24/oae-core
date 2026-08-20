#!/usr/bin/env python3
"""Validate aggregate coverage from a coverage.py JSON report."""

import argparse
import json
from pathlib import Path

DEFAULT_THRESHOLD = 70.0


def coverage_percent(report_path: Path) -> float:
    """Read the aggregate percentage from a coverage.py JSON report."""
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        value = payload["totals"]["percent_covered"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ValueError(f"Unable to read coverage percentage from {report_path}") from exc
    if not isinstance(value, int | float):
        raise ValueError(f"Coverage percentage in {report_path} must be numeric")
    return float(value)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail when a coverage.py JSON report is below the required threshold."
    )
    parser.add_argument("--coverage-file", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    args = parser.parse_args()

    if not 0 <= args.threshold <= 100:
        parser.error("--threshold must be between 0 and 100")

    try:
        observed = coverage_percent(args.coverage_file)
    except ValueError as exc:
        print(f"Coverage check error: {exc}")
        return 2

    print(f"Coverage: {observed:.2f}% (required: {args.threshold:.2f}%)")
    if observed < args.threshold:
        print("Coverage threshold check failed.")
        return 1
    print("Coverage threshold check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

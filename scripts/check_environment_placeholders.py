#!/usr/bin/env python3
"""Validate all declared OAE environment placeholders before a staging-host handoff.

The report intentionally contains variable names, categories, readiness status, and
remediation reasons only. It never renders environment values, including secrets.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from importlib import import_module
from pathlib import Path

preflight = import_module(
    ".staging_preflight" if __package__ else "staging_preflight",
    package=__package__,
)

REFERENCE_PATTERN = r"\$\{([A-Z][A-Z0-9_]*)\}"


@dataclass(frozen=True)
class VariableReadiness:
    name: str
    category: str
    status: str
    detail: str


def category_for(key: str) -> str:
    """Classify a variable without reading or revealing its value."""
    upper_key = key.upper()
    if preflight.SENSITIVE_KEY_PATTERN.search(upper_key):
        return "sensitive"
    if upper_key.startswith(("POSTGRES_", "DATABASE_")):
        return "database"
    if upper_key in {"API_DOMAIN", "ALLOWED_HOSTS", "CORS_ORIGINS", "CADDY_EMAIL"}:
        return "network"
    return "runtime"


def unresolved_reason(key: str, value: str, values: dict[str, str]) -> str | None:
    """Return a non-secret readiness reason, if a variable cannot be handed off."""
    if not value.strip():
        return "Value is empty."
    if preflight.PLACEHOLDER_PATTERN.search(value):
        return "Value matches a placeholder pattern."

    references = set(re.findall(REFERENCE_PATTERN, value))
    unresolved_references = [
        reference
        for reference in sorted(references)
        if reference not in values
        or not values[reference].strip()
        or preflight.PLACEHOLDER_PATTERN.search(values[reference])
    ]
    if unresolved_references:
        return f"Depends on unresolved variable(s): {', '.join(unresolved_references)}."
    return None


def assess_values(values: dict[str, str]) -> list[VariableReadiness]:
    """Assess every declared variable plus all required keys without showing values."""
    all_keys = sorted(set(preflight.REQUIRED_KEYS).union(values))
    readiness: list[VariableReadiness] = []
    for key in all_keys:
        if key not in values:
            readiness.append(
                VariableReadiness(key, category_for(key), "FAIL", "Required variable is missing.")
            )
            continue
        reason = unresolved_reason(key, values[key], values)
        readiness.append(
            VariableReadiness(
                key,
                category_for(key),
                "FAIL" if reason else "PASS",
                reason or "Value is configured without a detected placeholder.",
            )
        )
    return readiness


def build_report(env_file: Path) -> dict[str, object]:
    """Build a JSON-safe environment handoff report without emitting values."""
    if not env_file.exists():
        return {
            "environment_file": str(env_file),
            "status": "FAIL",
            "variables": [],
            "summary": {"pass": 0, "fail": 1},
            "reason": "Environment file does not exist.",
        }

    readiness = assess_values(preflight.parse_env_file(env_file))
    passed = sum(item.status == "PASS" for item in readiness)
    failed = len(readiness) - passed
    return {
        "environment_file": str(env_file),
        "status": "PASS" if not failed else "FAIL",
        "variables": [asdict(item) for item in readiness],
        "summary": {"pass": passed, "fail": failed},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--report", type=Path, help="Write the redacted JSON report to this path.")
    args = parser.parse_args()

    report = build_report(args.env_file)
    rendered = json.dumps(report, indent=2) + "\n"
    print(rendered, end="")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

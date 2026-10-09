"""Run a repeatable greenfield project-builder benchmark and emit JSON evidence.

Run from an installed OAE Core checkout:
    python benchmarks/greenfield_project_builder.py
    python benchmarks/greenfield_project_builder.py --workspace /tmp/oae-opportunityhub --output artifacts/greenfield-benchmark.json

Exit codes:
    0: generated project passed OAE's verification gate
    2: generation completed but the verification gate blocked the project
    1: benchmark could not complete (configuration/runtime error)
"""
from __future__ import annotations

import argparse
import json
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from oae.core.vertical_slice_mission import VerticalSliceMission


DEFAULT_NAME = "OpportunityHub"
DEFAULT_DESCRIPTION = (
    "Build a full-stack opportunity tracking application with a Python FastAPI "
    "backend, SQLite persistence, an executable health endpoint, typed API "
    "client, frontend pages, generated database/model/repository/API layers, "
    "environment configuration, Docker support, and pytest-based verification."
)


def _project_files(root: Path) -> list[str]:
    ignored = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache"}
    files: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or any(part in ignored for part in path.parts):
            continue
        files.append(path.relative_to(root).as_posix())
    return sorted(files)


def run_benchmark(
    root: Path,
    *,
    name: str = DEFAULT_NAME,
    description: str = DEFAULT_DESCRIPTION,
    mission: Any | None = None,
) -> dict[str, Any]:
    """Generate one clean project and return evidence without hiding failures."""
    root = root.resolve()
    if root.exists() and any(root.iterdir()):
        raise ValueError(f"Benchmark workspace must be empty: {root}")
    root.mkdir(parents=True, exist_ok=True)

    started = time.monotonic()
    result = (mission or VerticalSliceMission()).run(
        root,
        name=name,
        description=description,
        language="Python",
        framework="FastAPI",
        database="SQLite",
        testing_framework="pytest",
    )
    elapsed = round(time.monotonic() - started, 3)
    files = _project_files(root)
    verification = result.get("verification") or {}
    checks = verification.get("checks") or []
    failed_checks = [
        {
            "name": check.get("name", "unnamed check"),
            "detail": check.get("detail", ""),
        }
        for check in checks
        if not check.get("passed", False)
    ]
    contract = result.get("contract") or {}

    verified = result.get("verified") is True
    return {
        "benchmark": "oae-greenfield-project-builder-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": {
            "name": name,
            "description": description,
            "language": "Python",
            "framework": "FastAPI",
            "database": "SQLite",
            "testing_framework": "pytest",
        },
        "result": {
            "status": result.get("status", "unknown"),
            "verified": verified,
            "readiness_score": result.get("readiness_score", 0),
            "elapsed_seconds": elapsed,
            "file_count": len(files),
            "files": files,
            "workspace": str(root),
            "workspace_retained": True,
            "contract_passed": contract.get("passed") is True,
            "verification_status": verification.get("status", "not_run"),
            "failed_checks": failed_checks,
            "blockers": result.get("blockers") or [],
        },
        "acceptance": {
            "fresh_workspace": True,
            "generated_files_present": bool(files),
            "project_contract_passed": contract.get("passed") is True,
            "verification_passed": verified,
            "all_declared_checks_passed": verified and not failed_checks,
        },
        "limitations": [
            "This benchmark does not deploy the generated application.",
            "This benchmark does not by itself prove interrupted-run recovery.",
            "A verified scaffold is not a substitute for product-specific acceptance tests.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default=DEFAULT_NAME)
    parser.add_argument("--description", default=DEFAULT_DESCRIPTION)
    parser.add_argument(
        "--workspace",
        type=Path,
        help="Empty directory to generate into. If omitted, a retained temp directory is created.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for the JSON evidence report; report is always printed to stdout.",
    )
    args = parser.parse_args()

    try:
        workspace = args.workspace or Path(tempfile.mkdtemp(prefix="oae-greenfield-benchmark-"))
        report = run_benchmark(
            workspace,
            name=args.name,
            description=args.description,
        )
        encoded = json.dumps(report, indent=2, sort_keys=True)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(encoded + "\\n", encoding="utf-8")
        print(encoded)
        return 0 if report["result"]["verified"] else 2
    except Exception as exc:
        print(
            json.dumps(
                {
                    "benchmark": "oae-greenfield-project-builder-v1",
                    "status": "error",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
                indent=2,
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

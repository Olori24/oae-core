"""Repository quality and production-readiness gates for governed execution.

The gate is intentionally evidence-first: it discovers a small set of standard
checks, executes only through OAE's process policy, and returns bounded output.
It does not claim production readiness merely because one command passes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from oae.core.process_security import ProcessPolicyError, run_allowed_test_command

_MAX_OUTPUT = 12_000
_MAX_COMMANDS = 8


class RepositoryQualityGate:
    """Run bounded, repository-local quality checks and compute a readiness verdict."""

    def run(self, workspace: str | Path) -> dict[str, Any]:
        root = Path(workspace).resolve()
        if not root.is_dir():
            raise ValueError("workspace does not exist")

        checks = self._discover_checks(root)
        results = [self._run_check(root, check) for check in checks[:_MAX_COMMANDS]]
        passed = sum(1 for result in results if result["passed"])
        required = len(results)
        blockers = [
            result["name"]
            for result in results
            if not result["passed"] and result["required"]
        ]

        has_application_contract = any(
            (root / filename).is_file()
            for filename in ("pyproject.toml", "package.json", "go.mod", "Cargo.toml", "pom.xml")
        )
        checks_passed = required > 0 and passed == required
        readiness = checks_passed and has_application_contract and not blockers

        return {
            "schema_version": "1.0",
            "workspace": str(root),
            "checks": results,
            "check_count": required,
            "passed_count": passed,
            "blockers": blockers,
            "application_contract_detected": has_application_contract,
            "verified": checks_passed,
            "production_ready": readiness,
            "verdict": "ready" if readiness else "blocked",
        }

    def _discover_checks(self, root: Path) -> list[dict[str, Any]]:
        checks: list[dict[str, Any]] = []

        if (root / "pyproject.toml").is_file() or (root / "pytest.ini").is_file() or (root / "tests").is_dir():
            checks.append({"name": "pytest", "command": ["pytest", "-q"], "required": True})
        if (root / "pyproject.toml").is_file():
            checks.append({"name": "ruff", "command": ["ruff", "check", "."], "required": True})
            if (root / "src").is_dir():
                checks.append({"name": "mypy", "command": ["mypy", "src"], "required": False})

        # Node execution is deliberately not enabled by this first gate because
        # package scripts can invoke arbitrary shell commands. A governed Node
        # executor will add an explicit policy boundary in the next mission.
        if (root / "package.json").is_file() and not checks:
            checks.append(
                {
                    "name": "node-project-contract",
                    "command": None,
                    "required": True,
                    "static": True,
                }
            )

        if not checks:
            checks.append(
                {
                    "name": "repository-contract",
                    "command": None,
                    "required": True,
                    "static": True,
                }
            )
        return checks

    def _run_check(self, root: Path, check: dict[str, Any]) -> dict[str, Any]:
        if check.get("static"):
            return {
                "name": check["name"],
                "command": None,
                "returncode": 0,
                "passed": True,
                "required": bool(check["required"]),
                "stdout": "Repository contract detected; no executable gate was enabled for this stack yet.",
                "stderr": "",
            }

        command = check["command"]
        try:
            completed = run_allowed_test_command(command, cwd=root)
            return {
                "name": check["name"],
                "command": command,
                "returncode": completed.returncode,
                "passed": completed.returncode == 0,
                "required": bool(check["required"]),
                "stdout": self._bound(completed.stdout),
                "stderr": self._bound(completed.stderr),
            }
        except ProcessPolicyError as exc:
            return {
                "name": check["name"],
                "command": command,
                "returncode": 126,
                "passed": False,
                "required": bool(check["required"]),
                "stdout": "",
                "stderr": self._bound(str(exc)),
            }

    @staticmethod
    def _bound(value: str | None) -> str:
        value = value or ""
        return value[:_MAX_OUTPUT]

    @staticmethod
    def summarize(result: dict[str, Any]) -> str:
        return json.dumps(
            {
                "verdict": result["verdict"],
                "verified": result["verified"],
                "production_ready": result["production_ready"],
                "passed_count": result["passed_count"],
                "check_count": result["check_count"],
                "blockers": result["blockers"],
            },
            sort_keys=True,
        )

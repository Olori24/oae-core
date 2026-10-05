"""Deterministic production-readiness gate over accumulated OAE evidence."""
from __future__ import annotations

from typing import Any


def evaluate_production_readiness(
    *,
    quality_verified: bool,
    workspace_verified: bool,
    ci_status: str,
    change_set_synced: bool,
    pull_request_open: bool,
    deployment_verified: bool = False,
    rollback_verified: bool = False,
) -> dict[str, Any]:
    checks = {
        "quality_verified": bool(quality_verified),
        "workspace_verified": bool(workspace_verified),
        "ci_passed": ci_status == "passed",
        "change_set_synced": bool(change_set_synced),
        "pull_request_open": bool(pull_request_open),
        "deployment_verified": bool(deployment_verified),
        "rollback_verified": bool(rollback_verified),
    }
    blockers = [name for name, passed in checks.items() if not passed]
    return {
        "status": "ready" if not blockers else "blocked",
        "verified": not blockers,
        "checks": checks,
        "blockers": blockers,
        "required_for_production": list(checks),
    }

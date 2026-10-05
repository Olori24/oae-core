"""Deterministic engineering planning primitives for autonomous repository work.

The planner produces a bounded action graph from repository signals and an
engineering objective. It never executes commands or writes files.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class PlanStep:
    id: str
    action: str
    purpose: str
    requires: tuple[str, ...] = ()
    risk: str = "low"
    optional: bool = False


@dataclass(frozen=True)
class EngineeringPlan:
    version: str
    objective: str
    repository_kind: str
    steps: tuple[PlanStep, ...]
    completion_criteria: tuple[str, ...]
    blocked_reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "objective": self.objective,
            "repository_kind": self.repository_kind,
            "steps": [asdict(step) for step in self.steps],
            "completion_criteria": list(self.completion_criteria),
            "blocked_reasons": list(self.blocked_reasons),
        }


def build_engineering_plan(
    *,
    objective: str,
    repository_kind: str = "unknown",
    has_tests: bool = True,
    has_linter: bool = True,
    has_typecheck: bool = False,
    has_build: bool = False,
    security_required: bool = True,
) -> EngineeringPlan:
    objective = objective.strip()
    if not objective or len(objective) > 4000:
        raise ValueError("objective must contain 1 to 4000 characters")

    kind = repository_kind.strip().lower() or "unknown"
    if kind not in {"python", "node", "typescript", "mixed", "unknown"}:
        kind = "unknown"

    steps: list[PlanStep] = [
        PlanStep("inspect", "analyze_repository", "Confirm repository structure, entry points, dependencies, and existing quality signals."),
        PlanStep("baseline", "capture_baseline", "Run only supported read/verification operations before mutation.", ("inspect",)),
        PlanStep("implement", "mutate_workspace", f"Apply bounded changes required for the objective: {objective}", ("baseline",), "medium"),
        PlanStep("diff", "review_diff", "Inspect the complete governed diff before verification.", ("implement",)),
    ]

    verification: list[str] = []
    if kind in {"python", "mixed", "unknown"}:
        verification.append("python_compile")
    if has_linter:
        verification.append("ruff")
    if has_typecheck:
        verification.append("mypy")
    if has_tests:
        verification.append("pytest")
    if kind in {"node", "typescript", "mixed"} and has_build:
        verification.append("node_build")
    if security_required:
        verification.append("security_review")

    steps.append(PlanStep("verify", "verify_workspace", "Run the repository's approved verification set and stop on the first failure.", ("diff",), "medium"))
    steps.extend([
        PlanStep("repair", "repair_failures", "If verification fails, diagnose the bounded failure evidence and apply the smallest safe repair.", ("verify",), "high", True),
        PlanStep("reverify", "verify_workspace", "Re-run verification after a repair.", ("repair",), "medium", True),
        PlanStep("commit", "commit_change_set", "Create a governed commit only after verification succeeds.", ("verify",), "medium"),
        PlanStep("sync", "sync_github", "Synchronize the verified commit to a GitHub branch without force pushing.", ("commit",), "high"),
        PlanStep("pr", "create_pull_request", "Open a reviewable pull request containing the change-set evidence.", ("sync",), "high"),
    ])

    blocked: list[str] = []
    if not verification:
        blocked.append("No supported verification command is available.")
    criteria = (
        "objective implemented in the governed workspace",
        "diff reviewed",
        "verification completed successfully",
        "commit created from the verified worktree",
        "GitHub synchronization completed without force update",
        "pull request created for human/CI review",
    )
    return EngineeringPlan("1.0", objective, kind, tuple(steps), criteria, tuple(blocked))

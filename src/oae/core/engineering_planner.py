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
    inputs: dict[str, Any] | None = None


@dataclass(frozen=True)
class EngineeringPlan:
    version: str
    objective: str
    repository_kind: str
    steps: tuple[PlanStep, ...]
    completion_criteria: tuple[str, ...]
    blocked_reasons: tuple[str, ...] = ()
    verification_commands: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "objective": self.objective,
            "repository_kind": self.repository_kind,
            "steps": [asdict(step) for step in self.steps],
            "completion_criteria": list(self.completion_criteria),
            "blocked_reasons": list(self.blocked_reasons),
            "verification_commands": list(self.verification_commands),
        }


def build_engineering_plan(
    *,
    objective: str,
    repository_kind: str = "unknown",
    has_tests: bool = True,
    has_linter: bool = True,
    has_typecheck: bool = False,
    has_build: bool = False,
    test_runner: str = "none",
    security_required: bool = True,
    greenfield: bool = False,
    action_inputs: dict[str, dict[str, Any]] | None = None,
) -> EngineeringPlan:
    objective = objective.strip()
    if not objective or len(objective) > 4000:
        raise ValueError("objective must contain 1 to 4000 characters")

    if test_runner not in {"none", "vitest", "jest"}:
        raise ValueError("test_runner must be none, vitest, or jest")
    action_inputs = action_inputs or {}
    if len(action_inputs) > 32 or any(not isinstance(v, dict) for v in action_inputs.values()):
        raise ValueError("action_inputs must contain at most 32 object entries")

    kind = repository_kind.strip().lower() or "unknown"
    if kind not in {"python", "node", "typescript", "mixed", "unknown"}:
        kind = "unknown"

    if greenfield:
        steps: list[PlanStep] = [
            PlanStep("baseline", "capture_baseline", "Confirm the generated greenfield scaffold is readable and ready for governed coding."),
            PlanStep("implement", "code_objective", f"Generate, apply, and verify bounded code changes for the objective: {objective}", ("baseline",), "high", False, {"objective": objective}),
        ]
    else:
        steps = [
            PlanStep("inspect", "analyze_repository", "Confirm repository structure, entry points, dependencies, and existing quality signals."),
            PlanStep("baseline", "capture_baseline", "Run only supported read/verification operations before mutation.", ("inspect",)),
            PlanStep("implement", "code_objective", f"Generate, apply, and verify bounded code changes for the objective: {objective}", ("baseline",), "high", False, {"objective": objective}),
            PlanStep("diff", "review_diff", "Inspect the complete governed diff before verification.", ("implement",)),
        ]

    verification: list[str] = []
    if kind in {"python", "mixed", "unknown"}:
        verification.append("python_compile")
    if has_linter and kind in {"python", "mixed", "unknown"}:
        verification.append("ruff")
    if has_linter and kind in {"node", "typescript", "mixed"}:
        verification.append("eslint_check")
    if has_typecheck:
        verification.append("mypy")
    if has_tests:
        verification.append("pytest")
    if kind in {"node", "typescript", "mixed"} and has_typecheck:
        verification.append("typescript_check")
    if test_runner == "vitest":
        verification.append("vitest_check")
    elif test_runner == "jest":
        verification.append("jest_check")

    steps.append(PlanStep("verify", "verify_workspace", "Run the approved verification set and stop on the first failure.", ("implement",) if greenfield else ("diff",), "medium"))
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
    return EngineeringPlan(
        "1.0",
        objective,
        kind,
        tuple(
            PlanStep(
                step.id, step.action, step.purpose, step.requires, step.risk, step.optional,
                action_inputs.get(step.id),
            )
            for step in steps
        ),
        criteria,
        tuple(blocked),
        tuple(verification),
    )

"""Bounded autonomous-agent control primitives.

The controller is a state machine, not an unrestricted code-execution agent.
It can select only actions represented by the governed engineering plan.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_ALLOWED_ACTIONS = {
    "analyze_repository",
    "capture_baseline",
    "mutate_workspace",
    "review_diff",
    "verify_workspace",
    "repair_failures",
    "commit_change_set",
    "sync_github",
    "create_pull_request",
}


@dataclass(frozen=True)
class AgentDecision:
    status: str
    action: str | None
    step_id: str | None
    reason: str
    remaining_steps: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "action": self.action,
            "step_id": self.step_id,
            "reason": self.reason,
            "remaining_steps": self.remaining_steps,
        }


def next_agent_decision(plan: dict[str, Any], completed_steps: list[str]) -> AgentDecision:
    steps = plan.get("steps")
    if not isinstance(steps, list) or len(steps) > 32:
        raise ValueError("plan must contain at most 32 steps")
    completed = set(completed_steps)
    for step in steps:
        if not isinstance(step, dict):
            continue
        step_id = step.get("id")
        action = step.get("action")
        requires = step.get("requires", [])
        if not isinstance(step_id, str) or not isinstance(action, str):
            continue
        if action not in _ALLOWED_ACTIONS:
            raise ValueError(f"plan contains unsupported agent action: {action}")
        if step_id in completed:
            continue
        if not all(req in completed for req in requires):
            continue
        return AgentDecision("ready", action, step_id, "next dependency-satisfied governed action", len(steps) - len(completed) - 1)
    if all(isinstance(step, dict) and step.get("id") in completed for step in steps):
        return AgentDecision("complete", None, None, "all planned steps are complete", 0)
    return AgentDecision("blocked", None, None, "no dependency-satisfied action is available", len(steps) - len(completed))

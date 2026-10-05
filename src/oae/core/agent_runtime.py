"""Durable-state transition rules for bounded autonomous engineering runs.

This module contains no filesystem, shell, Git, network, or model execution.
It is deliberately deterministic so persisted agent state cannot silently
escape the engineering policy boundary.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from oae.core.autonomous_agent import AgentDecision, next_agent_decision

MAX_STEPS = 32
MAX_REPAIRS = 3
MAX_EVIDENCE_ITEMS = 64
MAX_EVIDENCE_BYTES = 100_000


@dataclass(frozen=True)
class AgentRunState:
    run_id: str
    status: str
    plan: dict[str, Any]
    completed_steps: tuple[str, ...] = ()
    failed_step: str | None = None
    repair_count: int = 0
    evidence: tuple[dict[str, Any], ...] = ()

    def next_decision(self) -> AgentDecision:
        return next_agent_decision(self.plan, list(self.completed_steps))


def start_agent_run(
    *,
    run_id: str,
    plan: dict[str, Any],
    max_repairs: int = 2,
) -> AgentRunState:
    if not run_id or len(run_id) > 120:
        raise ValueError("run_id must contain 1 to 120 characters")
    steps = plan.get("steps")
    if not isinstance(steps, list) or not steps or len(steps) > MAX_STEPS:
        raise ValueError("plan must contain 1 to 32 steps")
    if not 0 <= max_repairs <= MAX_REPAIRS:
        raise ValueError(f"max_repairs must be between 0 and {MAX_REPAIRS}")
    resolved_plan = dict(plan)
    resolved_plan["max_repairs"] = max_repairs
    return AgentRunState(run_id=run_id, status="running", plan=resolved_plan)


def record_step_result(
    state: AgentRunState,
    *,
    step_id: str,
    success: bool,
    evidence: dict[str, Any] | None = None,
) -> AgentRunState:
    if state.status in {"complete", "failed", "blocked"}:
        raise ValueError(f"agent run is terminal: {state.status}")
    if not step_id or len(step_id) > 120:
        raise ValueError("step_id must contain 1 to 120 characters")

    plan_steps = state.plan.get("steps", [])
    step_ids = {
        step.get("id")
        for step in plan_steps
        if isinstance(step, dict) and isinstance(step.get("id"), str)
    }
    if step_id not in step_ids:
        raise ValueError("step_id is not present in the plan")

    completed = list(state.completed_steps)
    evidence_items = list(state.evidence)
    normalized_evidence = _bounded_evidence(step_id, success, evidence)

    if step_id in completed:
        previous = next(
            (item for item in evidence_items if item.get("step_id") == step_id),
            None,
        )
        if previous is not None and bool(previous.get("success")) == success:
            return state
        raise ValueError("conflicting duplicate result for an already completed step")

    if success:
        completed.append(step_id)
        evidence_items.append(normalized_evidence)
        decision = next_agent_decision(state.plan, completed)
        status = "complete" if decision.status == "complete" else "running"
        return AgentRunState(
            run_id=state.run_id,
            status=status,
            plan=state.plan,
            completed_steps=tuple(completed),
            failed_step=None,
            repair_count=state.repair_count,
            evidence=tuple(evidence_items[-MAX_EVIDENCE_ITEMS:]),
        )

    evidence_items.append(normalized_evidence)
    if step_id not in {"verify", "reverify"}:
        return AgentRunState(
            run_id=state.run_id,
            status="failed",
            plan=state.plan,
            completed_steps=tuple(completed),
            failed_step=step_id,
            repair_count=state.repair_count,
            evidence=tuple(evidence_items[-MAX_EVIDENCE_ITEMS:]),
        )

    if step_id == "reverify":
        completed = [item for item in completed if item not in {"repair", "reverify"}]
        completed.append("reverify_failed")

    repair_step = next(
        (
            step
            for step in plan_steps
            if isinstance(step, dict)
            and step.get("id") == "repair"
            and step.get("optional") is True
        ),
        None,
    )
    if repair_step is None or state.repair_count >= int(state.plan.get("max_repairs", 2)):
        return AgentRunState(
            run_id=state.run_id,
            status="failed",
            plan=state.plan,
            completed_steps=tuple(completed + ([] if "verify_failed" in completed else ["verify_failed"])),
            failed_step="verify",
            repair_count=state.repair_count,
            evidence=tuple(evidence_items[-MAX_EVIDENCE_ITEMS:]),
        )

    completed.extend(["verify", "verify_failed"])
    return AgentRunState(
        run_id=state.run_id,
        status="running",
        plan=state.plan,
        completed_steps=tuple(completed),
        failed_step="verify",
        repair_count=state.repair_count + 1,
        evidence=tuple(evidence_items[-MAX_EVIDENCE_ITEMS:]),
    )


def _bounded_evidence(step_id: str, success: bool, evidence: dict[str, Any] | None) -> dict[str, Any]:
    payload = dict(evidence or {})
    payload["step_id"] = step_id
    payload["success"] = success
    text = str(payload)
    if len(text.encode("utf-8")) > MAX_EVIDENCE_BYTES:
        raise ValueError("agent step evidence exceeds the bounded evidence limit")
    return payload

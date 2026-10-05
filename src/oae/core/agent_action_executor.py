"""Map autonomous decisions to existing governed engineering operations.

This is the execution boundary for the autonomous loop. It deliberately does
not expose a generic shell, arbitrary Python, or arbitrary HTTP capability.
"""
from __future__ import annotations

from typing import Any, Callable

_ALLOWED = {
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


class AgentActionBlocked(ValueError):
    """Raised when a planned action lacks the required governed inputs."""


def execute_agent_action(
    *,
    action: str,
    step: dict[str, Any],
    workspace_id: str,
    base_payload: dict[str, Any],
    invoke: Callable[[str, dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    if action not in _ALLOWED:
        raise AgentActionBlocked("Unsupported autonomous action.")
    if not isinstance(step, dict) or step.get("action") != action:
        raise AgentActionBlocked("Plan step does not match the requested action.")

    inputs = step.get("inputs", {})
    if inputs is None:
        inputs = {}
    if not isinstance(inputs, dict):
        raise AgentActionBlocked("Autonomous action inputs must be an object.")

    payload = dict(base_payload)
    payload["workspace_id"] = workspace_id
    payload.update(inputs)

    mapping = {
        "analyze_repository": "analyze",
        "capture_baseline": "verify",
        "mutate_workspace": "mutate",
        "review_diff": "diff",
        "verify_workspace": "verify",
        "repair_failures": "repair",
        "commit_change_set": "commit",
        "sync_github": "sync",
        "create_pull_request": "pull_request",
    }
    stage = mapping[action]

    if action == "analyze_repository":
        repository_url = payload.get("repository_url")
        if not isinstance(repository_url, str) or not repository_url:
            raise AgentActionBlocked("analyze_repository requires repository_url.")
        return invoke("analyze", {"repository_url": repository_url})

    if action in {"mutate_workspace", "repair_failures"}:
        mutation = payload.get("mutation")
        if not isinstance(mutation, dict):
            raise AgentActionBlocked(
                f"{action} requires an explicit governed mutation specification."
            )
        mutation_type = mutation.get("type")
        if mutation_type not in {"write", "delete", "branch"}:
            raise AgentActionBlocked("Mutation type is not allowlisted.")
        payload["stage"] = mutation_type
        payload.update({k: v for k, v in mutation.items() if k != "type"})
        return invoke("build", payload)

    if action == "capture_baseline":
        payload["stage"] = "verify"
        return invoke("build", payload)

    payload["stage"] = stage
    return invoke("build", payload)

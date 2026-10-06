import pytest

from oae.core.agent_action_executor import AgentActionBlocked, execute_agent_action


def test_verify_action_maps_to_governed_workspace_verification():
    calls = []

    def invoke(operation, payload):
        calls.append((operation, payload))
        return {"verified": True}

    result = execute_agent_action(
        action="verify_workspace",
        step={"id": "verify", "action": "verify_workspace"},
        workspace_id="w1",
        base_payload={"commands": ["pytest"]},
        invoke=invoke,
    )

    assert result["verified"] is True
    assert calls[0][0] == "build"
    assert calls[0][1]["stage"] == "verify"
    assert calls[0][1]["workspace_id"] == "w1"


def test_mutation_requires_explicit_allowlisted_mutation():
    with pytest.raises(AgentActionBlocked, match="mutation specification"):
        execute_agent_action(
            action="mutate_workspace",
            step={"id": "implement", "action": "mutate_workspace"},
            workspace_id="w1",
            base_payload={},
            invoke=lambda *_: {},
        )


def test_mutation_cannot_select_an_arbitrary_stage():
    with pytest.raises(AgentActionBlocked, match="Mutation type"):
        execute_agent_action(
            action="mutate_workspace",
            step={"id": "implement", "action": "mutate_workspace", "inputs": {
                "mutation": {"type": "execute", "command": "rm -rf /"}
            }},
            workspace_id="w1",
            base_payload={},
            invoke=lambda *_: {},
        )


def test_analysis_requires_repository_url():
    with pytest.raises(AgentActionBlocked, match="repository_url"):
        execute_agent_action(
            action="analyze_repository",
            step={"id": "inspect", "action": "analyze_repository"},
            workspace_id="w1",
            base_payload={},
            invoke=lambda *_: {},
        )


def test_code_objective_maps_to_coding_execution():
    calls = []

    def invoke(operation, payload):
        calls.append((operation, payload))
        return {"verified": True}

    result = execute_agent_action(
        action="code_objective",
        step={"id": "implement", "action": "code_objective", "inputs": {"objective": "fix the bug"}},
        workspace_id="w1",
        base_payload={},
        invoke=invoke,
    )
    assert result["verified"] is True
    assert calls[0][0] == "build"
    assert calls[0][1]["stage"] == "coding_execute"
    assert calls[0][1]["objective"] == "fix the bug"

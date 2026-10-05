from oae.core.autonomous_agent import next_agent_decision
from oae.core.agent_action_executor import AgentActionBlocked, execute_agent_action


def test_code_objective_is_allowed():
    plan = {
        "steps": [
            {"id": "implement", "action": "code_objective", "requires": []}
        ]
    }
    decision = next_agent_decision(plan, [])
    assert decision.action == "code_objective"


def test_repair_requires_actual_failure_evidence():
    with __import__("pytest").raises(AgentActionBlocked):
        execute_agent_action(
            action="repair_failures",
            step={"id": "repair", "action": "repair_failures", "inputs": {}},
            workspace_id="w1",
            base_payload={"objective": "fix it"},
            invoke=lambda *_: {},
        )


def test_repair_maps_to_coding_repair_with_evidence():
    calls = []
    def invoke(operation, payload):
        calls.append((operation, payload))
        return {"verified": True}
    result = execute_agent_action(
        action="repair_failures",
        step={"id": "repair", "action": "repair_failures", "inputs": {}},
        workspace_id="w1",
        base_payload={
            "objective": "fix it",
            "failure_evidence": {"step_id": "verify", "success": False, "verification": [{"passed": False}]},
        },
        invoke=invoke,
    )
    assert result["verified"] is True
    assert calls[0][0] == "build"
    assert calls[0][1]["stage"] == "coding_repair"

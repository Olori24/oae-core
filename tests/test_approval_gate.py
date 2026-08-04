from oae.security import ApprovalGate, SecurityPolicy
from oae.security.request import ApprovalRequest


def test_sensitive_action_requires_approval():
    policy = SecurityPolicy()
    gate = ApprovalGate(policy)

    result = gate.approve(
        action="delete",
        target="src/oae/runtime.py",
        requester="Planner",
    )

    assert isinstance(result, ApprovalRequest)
    assert result.status == "PENDING"
    assert result.action == "delete"
    assert result.requester == "Planner"


def test_unknown_action_requires_approval():
    policy = SecurityPolicy()
    gate = ApprovalGate(policy)

    result = gate.approve(
        action="unknown",
        target="anything",
        requester="Planner",
    )

    assert isinstance(result, ApprovalRequest)
    assert result.status == "PENDING"

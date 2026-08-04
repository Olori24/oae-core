from oae.security import ApprovalGate, SecurityPolicy


def test_approval_gate_blocks_sensitive_actions():
    policy = SecurityPolicy()
    gate = ApprovalGate(policy)

    assert gate.approve("delete") is False
    assert gate.approve("force_push") is False
    assert gate.approve("shell") is False


def test_unknown_action_is_denied():
    policy = SecurityPolicy()
    gate = ApprovalGate(policy)

    assert gate.approve("unknown") is False
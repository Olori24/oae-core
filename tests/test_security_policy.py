from oae.security import SecurityPolicy


def test_default_security_policy():
    policy = SecurityPolicy()

    assert policy.can_delete() is False
    assert policy.can_force_push() is False
    assert policy.can_execute_shell() is False
    assert policy.require_human_approval is True

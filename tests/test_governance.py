from oae.governance.engine import GovernanceEngine


def test_governance_lifecycle():

    engine = GovernanceEngine()

    assert engine.ready() is False

    result = engine.initialize()

    assert result.approved is True
    assert engine.ready() is True

    engine.shutdown()

    assert engine.ready() is False

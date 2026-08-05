from oae.core.decision_engine import DecisionEngine


def test_high_confidence_low_risk():
    engine = DecisionEngine()

    decision = engine.evaluate(
        action="read",
        confidence=0.95,
    )

    assert decision.action == "read"
    assert decision.confidence == 0.95
    assert decision.risk == "LOW"
    assert decision.requires_approval is False


def test_low_confidence_requires_approval():
    engine = DecisionEngine()

    decision = engine.evaluate(
        action="read",
        confidence=0.60,
    )

    assert decision.risk == "LOW"
    assert decision.requires_approval is True


def test_high_risk_requires_approval():
    engine = DecisionEngine()

    decision = engine.evaluate(
        action="delete",
        confidence=0.99,
    )

    assert decision.risk == "HIGH"
    assert decision.requires_approval is True
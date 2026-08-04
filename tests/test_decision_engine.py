from oae.core.decision_engine import DecisionEngine


def test_high_confidence_does_not_require_approval():
    engine = DecisionEngine()

    decision = engine.evaluate(
        action="refactor",
        confidence=0.95,
    )

    assert decision.action == "refactor"
    assert decision.confidence == 0.95
    assert decision.requires_approval is False


def test_low_confidence_requires_approval():
    engine = DecisionEngine()

    decision = engine.evaluate(
        action="delete",
        confidence=0.60,
    )

    assert decision.requires_approval is True
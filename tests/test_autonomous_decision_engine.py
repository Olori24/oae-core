from oae.core.autonomous_decision_engine import (
    AutonomousDecisionEngine,
)


def test_creation():
    engine = AutonomousDecisionEngine()

    assert engine is not None


def test_security_decision():
    engine = AutonomousDecisionEngine()

    result = engine.decide(
        "Fix security vulnerability",
        health_score=80,
    )

    assert result["approved"] is True
    assert result["risk"] == "HIGH"


def test_low_health():
    engine = AutonomousDecisionEngine()

    result = engine.decide(
        "Improve documentation",
        health_score=40,
    )

    assert result["approved"] is False


def test_confidence():
    engine = AutonomousDecisionEngine()

    result = engine.decide(
        "Improve tests",
        health_score=90,
    )

    assert result["confidence"] >= 0.90


def test_verification_plan():
    engine = AutonomousDecisionEngine()

    result = engine.decide(
        "Any mission",
        health_score=90,
    )

    assert len(result["verification_plan"]) == 3


def test_reason_exists():
    engine = AutonomousDecisionEngine()

    result = engine.decide(
        "Refactor authentication",
        health_score=85,
    )

    assert result["reason"]
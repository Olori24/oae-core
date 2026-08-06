from oae.core.engineering_consciousness import (
    EngineeringConsciousness,
)


def test_creation():
    engine = EngineeringConsciousness()

    assert engine is not None


def test_objective():
    engine = EngineeringConsciousness()

    result = engine.evaluate("Fix authentication")

    assert result["objective"] == "Fix authentication"


def test_security_risk():
    engine = EngineeringConsciousness()

    result = engine.evaluate("Fix security issue")

    assert result["risk"] == "HIGH"


def test_confidence():
    engine = EngineeringConsciousness()

    result = engine.evaluate("Improve tests")

    assert result["confidence"] >= 0.90


def test_verification():
    engine = EngineeringConsciousness()

    result = engine.evaluate("Anything")

    assert len(result["verification_plan"]) == 3
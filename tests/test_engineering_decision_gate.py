from oae.core.engineering_decision_gate import EngineeringDecisionGate


def test_increase_verification_holds_mission():
    gate = EngineeringDecisionGate()

    result = gate.evaluate(
        "Authentication",
        {
            "recommendation": "increase_verification",
            "confidence": 0.8,
        },
    )

    assert result.decision == "hold"


def test_historical_failures_require_review():
    gate = EngineeringDecisionGate()

    result = gate.evaluate(
        "Database",
        {
            "recommendation": "review_historical_failures",
            "confidence": 0.5,
        },
    )

    assert result.decision == "review"


def test_no_history_requires_review():
    gate = EngineeringDecisionGate()

    result = gate.evaluate(
        "New subsystem",
        {
            "recommendation": "no_historical_evidence",
            "confidence": 0.0,
        },
    )

    assert result.decision == "review"


def test_successful_history_allows_proceed():
    gate = EngineeringDecisionGate()

    result = gate.evaluate(
        "API",
        {
            "recommendation": "proceed_with_standard_verification",
            "confidence": 1.0,
        },
    )

    assert result.decision == "proceed"


def test_decision_serializes():
    gate = EngineeringDecisionGate()

    result = gate.evaluate(
        "API",
        {
            "recommendation": "proceed_with_standard_verification",
            "confidence": 1.0,
        },
    )

    data = result.to_dict()

    assert data["mission"] == "API"
    assert data["decision"] == "proceed"
    assert data["recommendation"]["confidence"] == 1.0

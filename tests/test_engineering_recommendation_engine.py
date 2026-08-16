from math import isclose

from oae.core.engineering_ledger import EngineeringLedger
from oae.core.engineering_memory import EngineeringMemory
from oae.core.engineering_recommendation_engine import (
    EngineeringRecommendationEngine,
)


def make_engine():
    ledger = EngineeringLedger()
    memory = EngineeringMemory(ledger)
    return ledger, EngineeringRecommendationEngine(memory)


def test_creation():
    _, engine = make_engine()

    assert engine is not None


def test_no_historical_evidence():
    _, engine = make_engine()

    result = engine.recommend("Authentication")

    assert result["recommendation"] == "no_historical_evidence"
    assert result["confidence"] == 0.0


def test_failed_history_recommends_verification():
    ledger, engine = make_engine()

    ledger.record("MISSION_FAILED", "Authentication deployment failed")
    ledger.record("MISSION_FAILED", "Authentication tests failed")
    ledger.record("MISSION_COMPLETED", "Authentication eventually verified")

    result = engine.recommend("Authentication")

    assert result["recommendation"] == "increase_verification"
    assert isclose(result["confidence"], 2 / 3)


def test_mixed_history_recommends_review():
    ledger, engine = make_engine()

    ledger.record("MISSION_FAILED", "Database migration failed")
    ledger.record("MISSION_COMPLETED", "Database migration verified")

    result = engine.recommend("Database")

    assert result["recommendation"] == "review_historical_failures"
    assert result["confidence"] == 0.5


def test_successful_history_recommends_standard_verification():
    ledger, engine = make_engine()

    ledger.record("MISSION_COMPLETED", "API deployment verified")
    ledger.record("MISSION_COMPLETED", "API integration verified")

    result = engine.recommend("API")

    assert result["recommendation"] == "proceed_with_standard_verification"
    assert result["confidence"] == 1.0


def test_recommendation_is_advisory():
    ledger, engine = make_engine()

    ledger.record("MISSION_FAILED", "Authentication failed")

    result = engine.recommend("Authentication")

    assert "execute" not in result["recommendation"]
    assert "dispatch" not in result["recommendation"]

from oae.core.opportunity_intelligence_explanation import (
    OpportunityIntelligenceExplanation,
)


def make_opportunity():
    return {
        "title": "World Bank Grant",
        "intelligence_score": 92.5,
        "intelligence": {
            "score": 92.5,
            "eligible": True,
            "deadline_status": "open",
            "signals": {
                "fit": 95,
                "funding": 100,
                "verification": 100,
                "type": 100,
                "completeness": 100,
                "source_reliability": 100,
                "deadline": 100,
            },
        },
    }


def test_explanation_returns_score():
    engine = OpportunityIntelligenceExplanation()

    result = engine.explain(make_opportunity())

    assert result["score"] == 92.5


def test_explanation_identifies_positive_signals():
    engine = OpportunityIntelligenceExplanation()

    result = engine.explain(make_opportunity())

    assert "positive_signals" in result
    assert "fit" in result["positive_signals"]
    assert "funding" in result["positive_signals"]
    assert "verification" in result["positive_signals"]


def test_explanation_contains_recommendation_context():
    engine = OpportunityIntelligenceExplanation()

    result = engine.explain(make_opportunity())

    assert "eligibility" in result
    assert result["eligibility"] == "eligible"
    assert result["deadline"] == "open"


def test_explanation_generates_summary():
    engine = OpportunityIntelligenceExplanation()

    result = engine.explain(make_opportunity())

    assert "summary" in result
    assert isinstance(result["summary"], str)
    assert len(result["summary"]) > 0


def test_explanation_handles_missing_opportunity():
    engine = OpportunityIntelligenceExplanation()

    result = engine.explain(None)

    assert result["score"] == 0
    assert result["positive_signals"] == []
    assert result["eligibility"] == "unknown"
    assert result["deadline"] == "unknown"


def test_expired_opportunity_is_not_described_as_open():
    engine = OpportunityIntelligenceExplanation()

    opportunity = make_opportunity()
    opportunity["intelligence"]["deadline_status"] = "expired"

    result = engine.explain(opportunity)

    assert result["deadline"] == "expired"
    assert "open" not in result["summary"].lower()


def test_unknown_deadline_is_explicit():
    engine = OpportunityIntelligenceExplanation()

    opportunity = make_opportunity()
    opportunity["intelligence"]["deadline_status"] = "unknown"

    result = engine.explain(opportunity)

    assert result["deadline"] == "unknown"
    assert "unknown" in result["summary"].lower()


def test_explanation_does_not_change_score():
    engine = OpportunityIntelligenceExplanation()

    opportunity = make_opportunity()
    original_score = opportunity["intelligence"]["score"]

    engine.explain(opportunity)

    assert opportunity["intelligence"]["score"] == original_score

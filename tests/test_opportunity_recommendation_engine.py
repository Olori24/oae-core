from oae.core.opportunity_recommendation_engine import (
    OpportunityRecommendationEngine,
)


def make_opportunity(
    title,
    score,
    eligible=True,
    source_reliability="official",
):
    return {
        "title": title,
        "intelligence_score": score,
        "intelligence": {
            "score": score,
            "eligible": eligible,
            "deadline_status": "open",
            "signals": {
                "fit": 95,
                "funding": 100,
                "verification": 100,
                "type": 100,
                "completeness": 100,
                "source_reliability": (
                    100 if source_reliability == "official" else 20
                ),
                "deadline": 100,
            },
        },
    }


def test_high_score_eligible_opportunity_is_prioritized():
    engine = OpportunityRecommendationEngine()

    result = engine.recommend(
        [make_opportunity("Strong Grant", 92)],
    )

    assert result["recommendation"] == "prioritize"
    assert result["opportunity"]["title"] == "Strong Grant"
    assert result["confidence"] > 0


def test_medium_score_opportunity_requires_review():
    engine = OpportunityRecommendationEngine()

    result = engine.recommend(
        [make_opportunity("Moderate Grant", 65)],
    )

    assert result["recommendation"] == "review"


def test_low_score_opportunity_is_deprioritized():
    engine = OpportunityRecommendationEngine()

    result = engine.recommend(
        [make_opportunity("Weak Grant", 35)],
    )

    assert result["recommendation"] == "deprioritize"


def test_ineligible_opportunity_is_not_prioritized():
    engine = OpportunityRecommendationEngine()

    result = engine.recommend(
        [make_opportunity("Ineligible Grant", 95, eligible=False)],
    )

    assert result["recommendation"] != "prioritize"


def test_expired_opportunity_is_not_prioritized():
    engine = OpportunityRecommendationEngine()

    opportunity = make_opportunity("Expired Grant", 95)
    opportunity["intelligence"]["deadline_status"] = "expired"

    result = engine.recommend([opportunity])

    assert result["recommendation"] != "prioritize"


def test_empty_opportunity_list_requires_review():
    engine = OpportunityRecommendationEngine()

    result = engine.recommend([])

    assert result["recommendation"] == "review"
    assert result["opportunity"] is None


def test_recommendation_is_advisory():
    engine = OpportunityRecommendationEngine()

    result = engine.recommend(
        [make_opportunity("Strong Grant", 95)],
    )

    assert result["recommendation"] in {
        "prioritize",
        "review",
        "deprioritize",
    }

    assert "execute" not in result["recommendation"]
    assert "apply" not in result["recommendation"]
    assert "submit" not in result["recommendation"]

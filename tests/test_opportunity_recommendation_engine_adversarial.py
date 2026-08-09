from oae.core.opportunity_recommendation_engine import (
    OpportunityRecommendationEngine,
)


def make_opportunity(
    title="Opportunity",
    score=90,
    eligible=True,
    deadline_status="open",
):
    return {
        "title": title,
        "intelligence_score": score,
        "intelligence": {
            "score": score,
            "eligible": eligible,
            "deadline_status": deadline_status,
        },
    }


def test_none_input_requires_review():
    engine = OpportunityRecommendationEngine()

    result = engine.recommend(None)

    assert result["recommendation"] == "review"
    assert result["opportunity"] is None
    assert result["confidence"] == 0.0


def test_invalid_score_is_deprioritized():
    engine = OpportunityRecommendationEngine()

    opportunity = make_opportunity()
    opportunity["intelligence_score"] = "not-a-number"

    result = engine.recommend([opportunity])

    assert result["recommendation"] == "deprioritize"


def test_missing_intelligence_is_not_prioritized():
    engine = OpportunityRecommendationEngine()

    opportunity = {
        "title": "Incomplete Opportunity",
        "intelligence_score": 95,
    }

    result = engine.recommend([opportunity])

    assert result["recommendation"] != "prioritize"


def test_unknown_deadline_is_not_assumed_open():
    engine = OpportunityRecommendationEngine()

    result = engine.recommend(
        [
            make_opportunity(
                score=95,
                deadline_status="unknown",
            )
        ]
    )

    assert result["recommendation"] != "prioritize"


def test_expired_high_score_is_deprioritized():
    engine = OpportunityRecommendationEngine()

    result = engine.recommend(
        [
            make_opportunity(
                score=100,
                deadline_status="expired",
            )
        ]
    )

    assert result["recommendation"] == "deprioritize"


def test_ineligible_high_score_is_deprioritized():
    engine = OpportunityRecommendationEngine()

    result = engine.recommend(
        [
            make_opportunity(
                score=100,
                eligible=False,
            )
        ]
    )

    assert result["recommendation"] == "deprioritize"


def test_multiple_opportunities_use_highest_ranked_item():
    engine = OpportunityRecommendationEngine()

    opportunities = [
        make_opportunity(
            title="First",
            score=90,
        ),
        make_opportunity(
            title="Second",
            score=99,
        ),
    ]

    result = engine.recommend(opportunities)

    assert result["opportunity"]["title"] == "First"


def test_confidence_is_bounded():
    engine = OpportunityRecommendationEngine()

    for score in [0, 25, 50, 75, 100]:
        result = engine.recommend(
            [make_opportunity(score=score)]
        )

        assert 0.0 <= result["confidence"] <= 1.0

from oae.core.opportunity_ranker import OpportunityRanker


def test_ranker_returns_opportunities_in_score_order():
    ranker = OpportunityRanker()

    opportunities = [
        {
            "title": "Moderate Grant",
            "eligible_countries": "Nigeria",
            "opportunity_type": "grant",
            "funding_amount": 25000,
            "verification_status": "verified",
            "fit_score": 70,
            "deadline": "2099-12-31",
        },
        {
            "title": "Strong Grant",
            "eligible_countries": "Nigeria",
            "opportunity_type": "grant",
            "funding_amount": 100000,
            "verification_status": "verified",
            "fit_score": 95,
            "deadline": "2099-12-31",
        },
    ]

    ranked = ranker.rank(opportunities, country="Nigeria")

    assert ranked[0]["title"] == "Strong Grant"
    assert ranked[1]["title"] == "Moderate Grant"


def test_ranker_exposes_intelligence_score():
    ranker = OpportunityRanker()

    opportunities = [
        {
            "title": "Verified Grant",
            "eligible_countries": "Nigeria",
            "opportunity_type": "grant",
            "funding_amount": 50000,
            "verification_status": "verified",
            "fit_score": 95,
            "deadline": "2099-12-31",
        }
    ]

    ranked = ranker.rank(opportunities, country="Nigeria")

    assert "intelligence_score" in ranked[0]
    assert "intelligence" in ranked[0]
    assert ranked[0]["intelligence"]["eligible"] is True


def test_ranker_does_not_mutate_original_opportunities():
    ranker = OpportunityRanker()

    opportunity = {
        "title": "Grant",
        "eligible_countries": "Nigeria",
        "opportunity_type": "grant",
        "funding_amount": 50000,
        "verification_status": "verified",
        "fit_score": 90,
        "deadline": "2099-12-31",
    }

    original_keys = set(opportunity.keys())

    ranker.rank([opportunity], country="Nigeria")

    assert set(opportunity.keys()) == original_keys


def test_ranker_handles_empty_input():
    ranker = OpportunityRanker()

    assert ranker.rank([], country="Nigeria") == []

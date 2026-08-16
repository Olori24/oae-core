from oae.core.opportunity_ranker import OpportunityRanker


def make_opportunity(title, **overrides):
    opportunity = {
        "title": title,
        "eligible_countries": "Nigeria",
        "opportunity_type": "grant",
        "funding_amount": 50000,
        "verification_status": "verified",
        "fit_score": 90,
        "deadline": "2099-12-31",
    }
    opportunity.update(overrides)
    return opportunity


def test_none_input_returns_empty_list():
    ranker = OpportunityRanker()

    assert ranker.rank(None, country="Nigeria") == []


def test_single_opportunity_is_ranked():
    ranker = OpportunityRanker()

    ranked = ranker.rank(
        [make_opportunity("Single Grant")],
        country="Nigeria",
    )

    assert len(ranked) == 1
    assert ranked[0]["title"] == "Single Grant"


def test_equal_scores_preserve_input_order():
    ranker = OpportunityRanker()

    opportunities = [
        make_opportunity("First"),
        make_opportunity("Second"),
    ]

    ranked = ranker.rank(opportunities, country="Nigeria")

    assert ranked[0]["title"] == "First"
    assert ranked[1]["title"] == "Second"


def test_ineligible_opportunity_is_ranked_lower():
    ranker = OpportunityRanker()

    opportunities = [
        make_opportunity("Ineligible", eligible_countries="Kenya"),
        make_opportunity("Eligible", fit_score=80),
    ]

    ranked = ranker.rank(opportunities, country="Nigeria")

    assert ranked[0]["title"] == "Eligible"
    assert ranked[1]["title"] == "Ineligible"


def test_expired_opportunity_is_penalized():
    ranker = OpportunityRanker()

    opportunities = [
        make_opportunity("Expired", deadline="2000-01-01"),
        make_opportunity("Open"),
    ]

    ranked = ranker.rank(opportunities, country="Nigeria")

    assert ranked[0]["title"] == "Open"
    assert ranked[1]["title"] == "Expired"


def test_duplicate_opportunities_are_preserved():
    ranker = OpportunityRanker()

    opportunity = make_opportunity("Duplicate")

    ranked = ranker.rank(
        [opportunity, opportunity],
        country="Nigeria",
    )

    assert len(ranked) == 2
    assert ranked[0]["title"] == "Duplicate"
    assert ranked[1]["title"] == "Duplicate"


def test_ranker_does_not_mutate_nested_input():
    ranker = OpportunityRanker()

    opportunity = make_opportunity(
        "Nested",
        eligible_countries=["Nigeria", "Ghana"],
    )

    original = {
        **opportunity,
        "eligible_countries": list(opportunity["eligible_countries"]),
    }

    ranker.rank([opportunity], country="Nigeria")

    assert opportunity == original

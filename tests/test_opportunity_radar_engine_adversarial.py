from oae.core.opportunity_radar_engine import OpportunityRadarEngine


def make_opportunity(
    title="Opportunity",
    score=90,
    eligible_countries="Nigeria",
    deadline="2099-12-31",
):
    return {
        "title": title,
        "eligible_countries": eligible_countries,
        "opportunity_type": "grant",
        "funding_amount": "50000",
        "application_url": "https://example.org/apply",
        "source_url": "https://www.worldbank.org/grants",
        "verification_status": "verified",
        "fit_score": score,
        "deadline": deadline,
    }


def test_none_input_is_safe():
    engine = OpportunityRadarEngine()

    result = engine.analyze(
        None,
        country="Nigeria",
    )

    assert result["opportunities"] == []
    assert result["recommendation"]["recommendation"] == "review"


def test_missing_country_does_not_crash():
    engine = OpportunityRadarEngine()

    result = engine.analyze(
        [make_opportunity()],
        country=None,
    )

    assert len(result["opportunities"]) == 1
    assert result["opportunities"][0]["intelligence"]["eligible"] is False


def test_malformed_opportunity_does_not_crash():
    engine = OpportunityRadarEngine()

    result = engine.analyze(
        [{}],
        country="Nigeria",
    )

    assert len(result["opportunities"]) == 1
    assert result["recommendation"]["recommendation"] in {
        "review",
        "deprioritize",
    }


def test_invalid_score_does_not_crash():
    engine = OpportunityRadarEngine()

    opportunity = make_opportunity()
    opportunity["fit_score"] = "not-a-number"

    result = engine.analyze(
        [opportunity],
        country="Nigeria",
    )

    assert len(result["opportunities"]) == 1


def test_expired_high_score_is_not_prioritized():
    engine = OpportunityRadarEngine()

    result = engine.analyze(
        [
            make_opportunity(
                score=100,
                deadline="2000-01-01",
            )
        ],
        country="Nigeria",
    )

    assert (
        result["recommendation"]["recommendation"]
        != "prioritize"
    )


def test_unknown_deadline_is_not_prioritized():
    engine = OpportunityRadarEngine()

    opportunity = make_opportunity(score=100)
    opportunity.pop("deadline")

    result = engine.analyze(
        [opportunity],
        country="Nigeria",
    )

    assert (
        result["recommendation"]["recommendation"]
        != "prioritize"
    )


def test_ineligible_high_score_is_not_prioritized():
    engine = OpportunityRadarEngine()

    result = engine.analyze(
        [
            make_opportunity(
                score=100,
                eligible_countries="Kenya",
            )
        ],
        country="Nigeria",
    )

    assert (
        result["recommendation"]["recommendation"]
        != "prioritize"
    )


def test_input_list_is_not_modified():
    engine = OpportunityRadarEngine()

    opportunity = make_opportunity()
    original = dict(opportunity)
    opportunities = [opportunity]

    engine.analyze(
        opportunities,
        country="Nigeria",
    )

    assert opportunities[0] == original


def test_multiple_opportunities_are_ranked():
    engine = OpportunityRadarEngine()

    opportunities = [
        make_opportunity("Low", score=40),
        make_opportunity("High", score=95),
        make_opportunity("Medium", score=70),
    ]

    result = engine.analyze(
        opportunities,
        country="Nigeria",
    )

    titles = [
        opportunity["title"]
        for opportunity in result["opportunities"]
    ]

    assert titles[0] == "High"

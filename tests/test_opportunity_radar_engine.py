from oae.core.opportunity_radar_engine import OpportunityRadarEngine


def make_opportunity(
    title,
    score=90,
    eligible_countries="Nigeria",
    deadline="2099-12-31",
    source_url="https://www.worldbank.org/grants",
):
    return {
        "title": title,
        "eligible_countries": eligible_countries,
        "opportunity_type": "grant",
        "funding_amount": "50000",
        "application_url": "https://example.org/apply",
        "source_url": source_url,
        "verification_status": "verified",
        "fit_score": score,
        "deadline": deadline,
    }


def test_radar_engine_returns_ranked_opportunities():
    engine = OpportunityRadarEngine()

    opportunities = [
        make_opportunity("Lower Grant", score=70),
        make_opportunity("Higher Grant", score=95),
    ]

    result = engine.analyze(
        opportunities,
        country="Nigeria",
    )

    assert "opportunities" in result
    assert len(result["opportunities"]) == 2
    assert result["opportunities"][0]["title"] == "Higher Grant"


def test_radar_engine_returns_recommendation():
    engine = OpportunityRadarEngine()

    result = engine.analyze(
        [make_opportunity("Strong Grant", score=95)],
        country="Nigeria",
    )

    assert "recommendation" in result
    assert result["recommendation"]["recommendation"] == "prioritize"


def test_radar_engine_preserves_intelligence_details():
    engine = OpportunityRadarEngine()

    result = engine.analyze(
        [make_opportunity("Official Grant", score=95)],
        country="Nigeria",
    )

    opportunity = result["opportunities"][0]

    assert "intelligence" in opportunity
    assert "signals" in opportunity["intelligence"]
    assert "source_reliability" in opportunity["intelligence"]["signals"]


def test_radar_engine_handles_empty_input():
    engine = OpportunityRadarEngine()

    result = engine.analyze(
        [],
        country="Nigeria",
    )

    assert result["opportunities"] == []
    assert result["recommendation"]["recommendation"] == "review"


def test_radar_engine_does_not_mutate_input():
    engine = OpportunityRadarEngine()

    opportunity = make_opportunity("Grant", score=95)
    original = dict(opportunity)

    engine.analyze(
        [opportunity],
        country="Nigeria",
    )

    assert opportunity == original
def test_radar_engine_returns_explanation():
    engine = OpportunityRadarEngine()

    result = engine.analyze(
        [make_opportunity("Strong Grant", score=95)],
        country="Nigeria",
    )

    assert "explanation" in result
    assert result["explanation"]["score"] > 0
    assert len(result["explanation"]["summary"]) > 0


def test_radar_engine_explanation_matches_top_opportunity():
    engine = OpportunityRadarEngine()

    result = engine.analyze(
        [
            make_opportunity("Lower Grant", score=70),
            make_opportunity("Higher Grant", score=95),
        ],
        country="Nigeria",
    )

    assert (
        result["explanation"]["score"]
        == result["opportunities"][0]["intelligence"]["score"]
    )


def test_radar_engine_explanation_handles_empty_input():
    engine = OpportunityRadarEngine()

    result = engine.analyze(
        [],
        country="Nigeria",
    )

    assert result["explanation"]["score"] == 0
    assert result["explanation"]["eligibility"] == "unknown"
def test_radar_engine_can_analyze_raw_opportunities():
    engine = OpportunityRadarEngine()

    raw_opportunities = [
        {
            "title": "Raw Grant",
            "eligible_countries": "Nigeria",
            "opportunity_type": "grant",
            "funding_amount": "50000",
            "application_url": "https://example.org/apply",
            "source_url": "https://www.worldbank.org/grants",
            "verification_status": "verified",
            "fit_score": 95,
            "deadline": "2099-12-31",
        }
    ]

    result = engine.analyze_raw(
        raw_opportunities,
        country="Nigeria",
    )

    assert len(result["opportunities"]) == 1
    assert result["opportunities"][0]["title"] == "Raw Grant"


def test_radar_engine_analyze_raw_handles_empty_input():
    engine = OpportunityRadarEngine()

    result = engine.analyze_raw(
        [],
        country="Nigeria",
    )

    assert result["opportunities"] == []
    assert result["recommendation"]["recommendation"] == "review"


def test_radar_engine_analyze_raw_does_not_mutate_input():
    engine = OpportunityRadarEngine()

    raw = [
        {
            "title": "  Raw Grant  ",
            "organization": "  World Bank  ",
            "eligible_countries": "Nigeria",
        }
    ]

    original = [dict(item) for item in raw]

    engine.analyze_raw(
        raw,
        country="Nigeria",
    )

    assert raw == original


def test_radar_engine_analyze_raw_normalizes_whitespace():
    engine = OpportunityRadarEngine()

    result = engine.analyze_raw(
        [
            {
                "title": "  Raw Grant  ",
                "organization": "  World Bank  ",
                "eligible_countries": "Nigeria",
                "opportunity_type": "grant",
                "funding_amount": "50000",
                "verification_status": "verified",
                "fit_score": 95,
                "deadline": "2099-12-31",
            }
        ],
        country="Nigeria",
    )

    opportunity = result["opportunities"][0]

    assert opportunity["title"] == "Raw Grant"
    assert opportunity["organization"] == "World Bank"

from oae.core.opportunity_intelligence_scorer import (
    OpportunityIntelligenceScorer,
)


def test_high_quality_opportunity_scores_high():
    scorer = OpportunityIntelligenceScorer()

    result = scorer.score(
        {
            "eligible_countries": "Nigeria,Ghana",
            "opportunity_type": "grant",
            "funding_amount": "50000",
            "application_url": "https://example.org/apply",
            "source_url": "https://example.org",
            "verification_status": "verified",
            "fit_score": 95,
        },
        country="Nigeria",
    )

    assert result["score"] >= 80
    assert result["eligible"] is True


def test_ineligible_country_scores_low():
    scorer = OpportunityIntelligenceScorer()

    result = scorer.score(
        {
            "eligible_countries": "Kenya,South Africa",
            "opportunity_type": "grant",
            "funding_amount": "50000",
            "verification_status": "verified",
            "fit_score": 95,
        },
        country="Nigeria",
    )

    assert result["eligible"] is False
    assert result["score"] < 50


def test_unverified_opportunity_is_penalized():
    scorer = OpportunityIntelligenceScorer()

    result = scorer.score(
        {
            "eligible_countries": "Nigeria",
            "opportunity_type": "grant",
            "funding_amount": "50000",
            "verification_status": "unverified",
            "fit_score": 95,
        },
        country="Nigeria",
    )

    assert result["score"] < 80


def test_missing_intelligence_is_not_treated_as_perfect():
    scorer = OpportunityIntelligenceScorer()

    result = scorer.score(
        {
            "eligible_countries": "Nigeria",
            "opportunity_type": "grant",
        },
        country="Nigeria",
    )

    assert result["score"] < 100


def test_future_deadline_is_viable():
    scorer = OpportunityIntelligenceScorer()

    result = scorer.score(
        {
            "eligible_countries": "Nigeria",
            "opportunity_type": "grant",
            "funding_amount": "50000",
            "verification_status": "verified",
            "fit_score": 95,
            "deadline": "2099-12-31",
        },
        country="Nigeria",
    )

    assert result["deadline_status"] == "open"


def test_past_deadline_is_penalized():
    scorer = OpportunityIntelligenceScorer()

    result = scorer.score(
        {
            "eligible_countries": "Nigeria",
            "opportunity_type": "grant",
            "funding_amount": "50000",
            "verification_status": "verified",
            "fit_score": 95,
            "deadline": "2000-01-01",
        },
        country="Nigeria",
    )

    assert result["deadline_status"] == "expired"
    assert result["score"] < 80


def test_missing_deadline_is_not_treated_as_open():
    scorer = OpportunityIntelligenceScorer()

    result = scorer.score(
        {
            "eligible_countries": "Nigeria",
            "opportunity_type": "grant",
            "funding_amount": "50000",
            "verification_status": "verified",
            "fit_score": 95,
        },
        country="Nigeria",
    )

    assert result["deadline_status"] == "unknown"


def test_opportunities_can_be_ranked_by_intelligence_score():
    scorer = OpportunityIntelligenceScorer()

    opportunities = [
        {
            "title": "Strong African Startup Grant",
            "eligible_countries": "Nigeria",
            "opportunity_type": "grant",
            "funding_amount": 50000,
            "verification_status": "verified",
            "fit_score": 95,
            "deadline": "2099-12-31",
            "application_url": "https://example.com/apply",
            "source_url": "https://example.com",
        },
        {
            "title": "Moderate Accelerator",
            "eligible_countries": "Nigeria",
            "opportunity_type": "accelerator",
            "funding_amount": 25000,
            "verification_status": "verified",
            "fit_score": 70,
            "deadline": "2099-12-31",
            "application_url": "https://example.com/apply",
            "source_url": "https://example.com",
        },
        {
            "title": "Expired Grant",
            "eligible_countries": "Nigeria",
            "opportunity_type": "grant",
            "funding_amount": 50000,
            "verification_status": "verified",
            "fit_score": 95,
            "deadline": "2000-01-01",
            "application_url": "https://example.com/apply",
            "source_url": "https://example.com",
        },
    ]

    ranked = sorted(
        opportunities,
        key=lambda opportunity: scorer.score(
            opportunity,
            "Nigeria",
        )["score"],
        reverse=True,
    )

    assert ranked[0]["title"] == "Strong African Startup Grant"
    assert ranked[1]["title"] == "Moderate Accelerator"
    assert ranked[2]["title"] == "Expired Grant"


def test_score_exposes_explainable_breakdown():
    scorer = OpportunityIntelligenceScorer()

    opportunity = {
        "title": "Strong African Startup Grant",
        "eligible_countries": "Nigeria",
        "opportunity_type": "grant",
        "funding_amount": 50000,
        "verification_status": "verified",
        "fit_score": 95,
        "deadline": "2099-12-31",
        "application_url": "https://example.com/apply",
        "source_url": "https://example.com",
    }

    result = scorer.score(
        opportunity,
        "Nigeria",
    )

    assert "score" in result
    assert "signals" in result

    signals = result["signals"]

    assert signals["fit"] == 95
    assert signals["funding"] == 100
    assert signals["verification"] == 100
    assert signals["type"] == 100
    assert signals["deadline"] == 100
    assert signals["completeness"] == 100


def test_source_reliability_is_exposed():
    scorer = OpportunityIntelligenceScorer()

    opportunity = {
        "title": "Verified African Grant",
        "eligible_countries": "Nigeria",
        "opportunity_type": "grant",
        "funding_amount": 50000,
        "verification_status": "verified",
        "source_reliability": "official",
        "fit_score": 95,
        "deadline": "2099-12-31",
        "application_url": "https://example.com/apply",
        "source_url": "https://example.com",
    }

    result = scorer.score(
        opportunity,
        "Nigeria",
    )

    assert "source_reliability" in result["signals"]
    assert result["signals"]["source_reliability"] == 100


def test_official_source_outranks_unknown_source():
    scorer = OpportunityIntelligenceScorer()

    official = {
        "title": "Official Grant",
        "eligible_countries": "Nigeria",
        "opportunity_type": "grant",
        "funding_amount": 25000,
        "verification_status": "verified",
        "source_reliability": "official",
        "fit_score": 85,
        "deadline": "2099-12-31",
        "application_url": "https://example.com/apply",
        "source_url": "https://example.com",
    }

    unknown = {
        **official,
        "title": "Unknown Source Grant",
        "source_reliability": "unknown",
    }

    official_score = scorer.score(
        official,
        "Nigeria",
    )["score"]

    unknown_score = scorer.score(
        unknown,
        "Nigeria",
    )["score"]

    assert official_score > unknown_score


def test_official_source_url_improves_opportunity_score():
    scorer = OpportunityIntelligenceScorer()

    base = {
        "title": "African Development Grant",
        "eligible_countries": ["Nigeria"],
        "opportunity_type": "grant",
        "funding_amount": 100000,
        "deadline": "2099-12-31",
        "application_url": "https://example.org/apply",
        "source_url": "https://www.afdb.org/opportunities",
        "verification_status": "verified",
        "fit_score": 80,
    }

    unknown = dict(
        base,
        source_url="https://random-example-site.com/grant",
    )

    official_result = scorer.score(
        base,
        "Nigeria",
    )

    unknown_result = scorer.score(
        unknown,
        "Nigeria",
    )

    assert official_result["score"] > unknown_result["score"]


def test_source_trust_signal_is_exposed_from_url():
    scorer = OpportunityIntelligenceScorer()

    opportunity = {
        "title": "World Bank Grant",
        "eligible_countries": ["Nigeria"],
        "opportunity_type": "grant",
        "funding_amount": 100000,
        "deadline": "2099-12-31",
        "application_url": "https://example.org/apply",
        "source_url": "https://www.worldbank.org/grants",
        "verification_status": "verified",
        "fit_score": 80,
    }

    result = scorer.score(
        opportunity,
        "Nigeria",
    )

    assert "source_reliability" in result["signals"]
    assert result["signals"]["source_reliability"] == 100

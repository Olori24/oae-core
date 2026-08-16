from oae.core.opportunity_intelligence_scorer import (
    OpportunityIntelligenceScorer,
)


def base_opportunity(**overrides):
    opportunity = {
        "title": "African Funding Opportunity",
        "eligible_countries": "Nigeria,Ghana,Kenya",
        "opportunity_type": "grant",
        "funding_amount": 50000,
        "verification_status": "verified",
        "fit_score": 90,
        "deadline": "2099-12-31",
        "application_url": "https://example.org/apply",
        "source_url": "https://example.org",
    }
    opportunity.update(overrides)
    return opportunity


def test_official_source_beats_unknown_source():
    scorer = OpportunityIntelligenceScorer()

    official = base_opportunity(
        source_url="https://www.worldbank.org/grants",
    )

    unknown = base_opportunity(
        source_url="https://random-example-site.com/grant",
    )

    official_score = scorer.score(official, "Nigeria")["score"]
    unknown_score = scorer.score(unknown, "Nigeria")["score"]

    assert official_score > unknown_score


def test_verified_beats_unverified():
    scorer = OpportunityIntelligenceScorer()

    verified = base_opportunity(
        verification_status="verified",
    )

    unverified = base_opportunity(
        verification_status="unverified",
    )

    verified_score = scorer.score(verified, "Nigeria")["score"]
    unverified_score = scorer.score(unverified, "Nigeria")["score"]

    assert verified_score > unverified_score


def test_open_deadline_beats_expired_deadline():
    scorer = OpportunityIntelligenceScorer()

    open_opportunity = base_opportunity(
        deadline="2099-12-31",
    )

    expired = base_opportunity(
        deadline="2000-01-01",
    )

    open_score = scorer.score(open_opportunity, "Nigeria")["score"]
    expired_score = scorer.score(expired, "Nigeria")["score"]

    assert open_score > expired_score


def test_ineligible_opportunity_is_heavily_penalized():
    scorer = OpportunityIntelligenceScorer()

    eligible = base_opportunity(
        eligible_countries="Nigeria,Ghana",
    )

    ineligible = base_opportunity(
        eligible_countries="Kenya,South Africa",
        funding_amount=500000,
        fit_score=100,
        verification_status="verified",
        source_url="https://www.worldbank.org/grants",
    )

    eligible_score = scorer.score(eligible, "Nigeria")["score"]
    ineligible_result = scorer.score(ineligible, "Nigeria")

    assert ineligible_result["eligible"] is False
    assert ineligible_result["score"] < eligible_score


def test_missing_intelligence_does_not_score_as_perfect():
    scorer = OpportunityIntelligenceScorer()

    incomplete = {
        "eligible_countries": "Nigeria",
        "opportunity_type": "grant",
    }

    result = scorer.score(incomplete, "Nigeria")

    assert result["score"] < 100


def test_official_url_exposes_source_trust_signal():
    scorer = OpportunityIntelligenceScorer()

    opportunity = base_opportunity(
        source_url="https://www.worldbank.org/grants",
    )

    result = scorer.score(opportunity, "Nigeria")

    assert result["signals"]["source_reliability"] == 100


def test_unknown_url_does_not_receive_official_trust():
    scorer = OpportunityIntelligenceScorer()

    opportunity = base_opportunity(
        source_url="https://random-example-site.com/grant",
    )

    result = scorer.score(opportunity, "Nigeria")

    assert result["signals"]["source_reliability"] < 100


def test_combined_high_quality_opportunity_beats_low_quality_opportunity():
    scorer = OpportunityIntelligenceScorer()

    strong = base_opportunity(
        source_url="https://www.afdb.org/opportunities",
        verification_status="verified",
        fit_score=95,
        funding_amount=100000,
        deadline="2099-12-31",
    )

    weak = base_opportunity(
        source_url="https://random-example-site.com/grant",
        verification_status="unverified",
        fit_score=50,
        funding_amount=10000,
        deadline="2000-01-01",
    )

    strong_score = scorer.score(strong, "Nigeria")["score"]
    weak_score = scorer.score(weak, "Nigeria")["score"]

    assert strong_score > weak_score

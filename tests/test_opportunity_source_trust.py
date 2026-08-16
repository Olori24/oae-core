from oae.core.opportunity_source_trust import OpportunitySourceTrust


def test_official_source_is_high_trust():
    trust = OpportunitySourceTrust()

    result = trust.evaluate(
        "https://www.worldbank.org/example-grant"
    )

    assert result["reliability"] == "official"
    assert result["score"] == 100
    assert result["confidence"] > 0


def test_unknown_source_is_low_trust():
    trust = OpportunitySourceTrust()

    result = trust.evaluate(
        "https://random-example-site.com/grant"
    )

    assert result["reliability"] == "unknown"
    assert result["score"] < 50


def test_missing_source_is_unknown():
    trust = OpportunitySourceTrust()

    result = trust.evaluate(None)

    assert result["reliability"] == "unknown"
    assert result["score"] == 0


def test_spoofed_official_domain_is_not_trusted():
    trust = OpportunitySourceTrust()

    result = trust.evaluate(
        "https://worldbank.org.evil-example.com/grant"
    )

    assert result["reliability"] == "unknown"
    assert result["score"] < 50


def test_official_domain_in_path_is_not_trusted():
    trust = OpportunitySourceTrust()

    result = trust.evaluate(
        "https://evil-example.com/worldbank.org/grant"
    )

    assert result["reliability"] == "unknown"
    assert result["score"] < 50


def test_official_subdomain_is_trusted():
    trust = OpportunitySourceTrust()

    result = trust.evaluate(
        "https://projects.worldbank.org/grant"
    )

    assert result["reliability"] == "official"
    assert result["score"] == 100


def test_trailing_dot_domain_is_trusted():
    trust = OpportunitySourceTrust()

    result = trust.evaluate(
        "https://worldbank.org./grant"
    )

    assert result["reliability"] == "official"
    assert result["score"] == 100


def test_malformed_url_is_safe():
    trust = OpportunitySourceTrust()

    result = trust.evaluate(
        "https://[invalid-url"
    )

    assert result["reliability"] == "unknown"
    assert result["score"] == 0


def test_missing_scheme_is_not_trusted():
    trust = OpportunitySourceTrust()

    result = trust.evaluate(
        "worldbank.org/grant"
    )

    assert result["reliability"] == "unknown"
    assert result["score"] == 0

def test_afdb_is_official_source():
    trust = OpportunitySourceTrust()

    result = trust.evaluate(
        "https://www.afdb.org/en/opportunities"
    )

    assert result["reliability"] == "official"
    assert result["score"] == 100


def test_un_domain_is_official_source():
    trust = OpportunitySourceTrust()

    result = trust.evaluate(
        "https://www.un.org/opportunities"
    )

    assert result["reliability"] == "official"
    assert result["score"] == 100


def test_african_government_domain_is_official_source():
    trust = OpportunitySourceTrust()

    result = trust.evaluate(
        "https://example.gov.ng/grants"
    )

    assert result["reliability"] == "official"
    assert result["score"] == 100


def test_subdomain_of_african_government_is_official():
    trust = OpportunitySourceTrust()

    result = trust.evaluate(
        "https://funding.example.gov.ng/grants"
    )

    assert result["reliability"] == "official"
    assert result["score"] == 100

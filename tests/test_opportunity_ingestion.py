from oae.core.opportunity_ingestion import OpportunityIngestion


def test_normalizes_basic_opportunity():
    ingestion = OpportunityIngestion()

    raw = {
        "title": "World Bank Grant",
        "organization": "World Bank",
        "eligible_countries": "Nigeria,Ghana",
        "opportunity_type": "grant",
        "funding_amount": "50000",
        "deadline": "2099-12-31",
        "application_url": "https://example.org/apply",
        "source_url": "https://www.worldbank.org/grants",
    }

    result = ingestion.normalize(raw)

    assert result["title"] == "World Bank Grant"
    assert result["organization"] == "World Bank"
    assert result["opportunity_type"] == "grant"
    assert result["source_url"] == "https://www.worldbank.org/grants"


def test_missing_optional_fields_get_safe_defaults():
    ingestion = OpportunityIngestion()

    result = ingestion.normalize(
        {
            "title": "Simple Grant",
        }
    )

    assert result["title"] == "Simple Grant"
    assert result["organization"] == ""
    assert result["eligible_countries"] == ""
    assert result["funding_amount"] == ""
    assert result["deadline"] == ""
    assert result["source_url"] == ""


def test_whitespace_is_normalized():
    ingestion = OpportunityIngestion()

    result = ingestion.normalize(
        {
            "title": "  World Bank Grant  ",
            "organization": "  World Bank ",
            "source_url": "  https://www.worldbank.org/grants  ",
        }
    )

    assert result["title"] == "World Bank Grant"
    assert result["organization"] == "World Bank"
    assert result["source_url"] == "https://www.worldbank.org/grants"


def test_none_input_returns_empty_opportunity():
    ingestion = OpportunityIngestion()

    result = ingestion.normalize(None)

    assert result["title"] == ""
    assert result["organization"] == ""
    assert result["source_url"] == ""


def test_non_dictionary_input_does_not_crash():
    ingestion = OpportunityIngestion()

    result = ingestion.normalize("invalid")

    assert result["title"] == ""
    assert result["source_url"] == ""


def test_normalizer_does_not_mutate_input():
    ingestion = OpportunityIngestion()

    raw = {
        "title": "  Grant  ",
        "organization": " World Bank ",
    }

    original = dict(raw)

    ingestion.normalize(raw)

    assert raw == original


def test_known_fields_are_preserved():
    ingestion = OpportunityIngestion()

    raw = {
        "title": "Grant",
        "organization": "Organization",
        "country": "Nigeria",
        "category": "Technology",
        "deadline": "2099-12-31",
        "url": "https://example.org",
        "description": "A funding opportunity",
        "eligible_countries": "Nigeria",
        "opportunity_type": "grant",
        "funding_amount": "100000",
        "application_url": "https://example.org/apply",
        "source_url": "https://example.org/source",
        "verification_status": "verified",
        "fit_score": 90,
    }

    result = ingestion.normalize(raw)

    for key, value in raw.items():
        assert result[key] == value
def test_normalizes_many_opportunities():
    ingestion = OpportunityIngestion()

    raw = [
        {"title": "Grant A"},
        {"title": "Grant B"},
    ]

    result = ingestion.normalize_many(raw)

    assert len(result) == 2
    assert result[0]["title"] == "Grant A"
    assert result[1]["title"] == "Grant B"


def test_normalize_many_empty_input_returns_empty_list():
    ingestion = OpportunityIngestion()

    assert ingestion.normalize_many([]) == []


def test_normalize_many_none_returns_empty_list():
    ingestion = OpportunityIngestion()

    assert ingestion.normalize_many(None) == []


def test_normalize_many_handles_mixed_input():
    ingestion = OpportunityIngestion()

    result = ingestion.normalize_many(
        [
            {"title": "Valid Grant"},
            None,
            "invalid",
            {"title": "Another Grant"},
        ]
    )

    assert len(result) == 4
    assert result[0]["title"] == "Valid Grant"
    assert result[1]["title"] == ""
    assert result[2]["title"] == ""
    assert result[3]["title"] == "Another Grant"


def test_normalize_many_does_not_mutate_input():
    ingestion = OpportunityIngestion()

    raw = [
        {"title": "  Grant A  "},
        {"title": "  Grant B  "},
    ]

    original = [dict(item) for item in raw]

    ingestion.normalize_many(raw)

    assert raw == original


def test_normalize_many_preserves_order():
    ingestion = OpportunityIngestion()

    raw = [
        {"title": "Third"},
        {"title": "First"},
        {"title": "Second"},
    ]

    result = ingestion.normalize_many(raw)

    assert [item["title"] for item in result] == [
        "Third",
        "First",
        "Second",
    ]

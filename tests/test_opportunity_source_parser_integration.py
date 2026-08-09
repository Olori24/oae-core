from oae.core.opportunity_ingestion import OpportunityIngestion
from oae.core.opportunity_source_parser import OpportunitySourceParser


def test_parser_output_can_be_ingested():
    parser = OpportunitySourceParser(
        field_mapping={
            "name": "title",
            "organization_name": "organization",
            "closing_date": "deadline",
            "apply_url": "application_url",
        }
    )

    ingestion = OpportunityIngestion()

    payload = {
        "results": [
            {
                "name": "AI Grant",
                "organization_name": "Example Foundation",
                "closing_date": "2099-12-31",
                "apply_url": "https://example.org/apply",
            }
        ]
    }

    parsed = parser.parse(payload)
    result = ingestion.normalize_many(parsed)

    assert len(result) == 1
    assert result[0]["title"] == "AI Grant"
    assert result[0]["organization"] == "Example Foundation"
    assert result[0]["deadline"] == "2099-12-31"
    assert result[0]["application_url"] == (
        "https://example.org/apply"
    )


def test_parser_and_ingestion_handle_empty_source():
    parser = OpportunitySourceParser(
        field_mapping={
            "name": "title",
        }
    )

    ingestion = OpportunityIngestion()

    parsed = parser.parse(
        {
            "results": []
        }
    )

    result = ingestion.normalize_many(parsed)

    assert result == []


def test_parser_and_ingestion_preserve_source_order():
    parser = OpportunitySourceParser(
        field_mapping={
            "name": "title",
        }
    )

    ingestion = OpportunityIngestion()

    payload = [
        {"name": "Third"},
        {"name": "First"},
        {"name": "Second"},
    ]

    parsed = parser.parse(payload)
    result = ingestion.normalize_many(parsed)

    assert [
        opportunity["title"]
        for opportunity in result
    ] == [
        "Third",
        "First",
        "Second",
    ]

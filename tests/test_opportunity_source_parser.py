from oae.core.opportunity_source_parser import (
    OpportunitySourceParser,
)


def test_parser_accepts_direct_list():
    parser = OpportunitySourceParser(
        field_mapping={
            "name": "title",
            "organization_name": "organization",
            "closing_date": "deadline",
        }
    )

    payload = [
        {
            "name": "AI Grant",
            "organization_name": "Example Foundation",
            "closing_date": "2099-12-31",
        }
    ]

    result = parser.parse(payload)

    assert result == [
        {
            "title": "AI Grant",
            "organization": "Example Foundation",
            "deadline": "2099-12-31",
        }
    ]


def test_parser_accepts_wrapped_results():
    parser = OpportunitySourceParser(
        field_mapping={
            "name": "title",
        }
    )

    payload = {
        "results": [
            {
                "name": "AI Grant",
            },
            {
                "name": "Startup Fellowship",
            },
        ]
    }

    result = parser.parse(payload)

    assert result == [
        {"title": "AI Grant"},
        {"title": "Startup Fellowship"},
    ]


def test_parser_returns_empty_list_for_invalid_payload():
    parser = OpportunitySourceParser(
        field_mapping={
            "name": "title",
        }
    )

    assert parser.parse(None) == []
    assert parser.parse("invalid") == []
    assert parser.parse(123) == []


def test_parser_returns_empty_list_for_invalid_results():
    parser = OpportunitySourceParser(
        field_mapping={
            "name": "title",
        }
    )

    assert parser.parse({"results": "invalid"}) == []


def test_parser_ignores_non_dictionary_items():
    parser = OpportunitySourceParser(
        field_mapping={
            "name": "title",
        }
    )

    payload = {
        "results": [
            {"name": "Grant A"},
            None,
            "invalid",
            {"name": "Grant B"},
        ]
    }

    result = parser.parse(payload)

    assert result == [
        {"title": "Grant A"},
        {"title": "Grant B"},
    ]


def test_parser_preserves_unmapped_fields():
    parser = OpportunitySourceParser(
        field_mapping={
            "name": "title",
        }
    )

    payload = [
        {
            "name": "Grant A",
            "description": "Funding for startups",
            "amount": 50000,
        }
    ]

    result = parser.parse(payload)

    assert result[0]["title"] == "Grant A"
    assert result[0]["description"] == "Funding for startups"
    assert result[0]["amount"] == 50000


def test_parser_does_not_mutate_payload():
    parser = OpportunitySourceParser(
        field_mapping={
            "name": "title",
        }
    )

    payload = [
        {
            "name": "  Grant A  ",
        }
    ]

    original = [
        dict(item)
        for item in payload
    ]

    parser.parse(payload)

    assert payload == original


def test_parser_normalizes_mapped_string_values():
    parser = OpportunitySourceParser(
        field_mapping={
            "name": "title",
            "organization_name": "organization",
        }
    )

    payload = [
        {
            "name": "  Grant A  ",
            "organization_name": "  Example Foundation ",
        }
    ]

    result = parser.parse(payload)

    assert result == [
        {
            "title": "Grant A",
            "organization": "Example Foundation",
        }
    ]

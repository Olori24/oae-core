from oae.core.opportunity_model_generator import OpportunityModelGenerator
from oae.core.schema_generator import SchemaGenerator


def test_opportunity_model_supports_intelligence_fields(tmp_path):
    OpportunityModelGenerator().generate(tmp_path)
    SchemaGenerator().generate(tmp_path)

    model = (
        tmp_path
        / "src"
        / "models"
        / "opportunity.py"
    ).read_text()

    schema = (
        tmp_path
        / "src"
        / "schemas"
        / "opportunity.py"
    ).read_text()

    required_fields = [
        "eligible_countries",
        "opportunity_type",
        "funding_amount",
        "application_url",
        "source_url",
        "verification_status",
        "fit_score",
    ]

    for field in required_fields:
        assert field in model, f"Missing model intelligence field: {field}"
        assert field in schema, f"Missing schema intelligence field: {field}"

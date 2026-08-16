from oae.core.opportunity_api_generator import (
    OpportunityApiGenerator,
)


def test_generate(tmp_path):
    OpportunityApiGenerator().generate(tmp_path)

    assert (
        tmp_path
        / "src"
        / "api"
        / "opportunities.py"
    ).exists()

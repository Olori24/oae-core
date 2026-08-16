from oae.core.opportunity_model_generator import (
    OpportunityModelGenerator,
)


def test_generate(tmp_path):
    OpportunityModelGenerator().generate(tmp_path)

    assert (
        tmp_path
        / "src"
        / "models"
        / "opportunity.py"
    ).exists()

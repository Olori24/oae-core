from oae.core.opportunity_repository_generator import (
    OpportunityRepositoryGenerator,
)


def test_generate(tmp_path):
    OpportunityRepositoryGenerator().generate(tmp_path)

    assert (
        tmp_path
        / "src"
        / "repositories"
        / "opportunity_repository.py"
    ).exists()

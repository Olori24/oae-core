from oae.core.engineering_executive_pipeline import (
    EngineeringExecutivePipeline,
)


def test_creation():
    pipeline = EngineeringExecutivePipeline()

    assert pipeline is not None


def test_execute(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    (repo / "app.py").write_text(
        """
class App:
    pass

def run():
    pass
"""
    )

    pipeline = EngineeringExecutivePipeline()

    result = pipeline.execute(repo)

    assert "intelligence" in result
    assert "diagnosis" in result
    assert "missions" in result
    assert len(result["missions"]) > 0

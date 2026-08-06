from oae.core.engineering_executive_pipeline import (
    EngineeringExecutivePipeline,
)


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

    report = pipeline.execute(repo)

    assert "diagnosis" in report
    assert "analysis" in report
    assert "recommendations" in report
    assert "recovery" in report

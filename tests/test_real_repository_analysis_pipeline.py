from oae.core.real_repository_analysis_pipeline import (
    RealRepositoryAnalysisPipeline,
)


def test_pipeline_creation():
    pipeline = RealRepositoryAnalysisPipeline()

    assert pipeline is not None


def test_pipeline(tmp_path):
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

    pipeline = RealRepositoryAnalysisPipeline()

    result = pipeline.analyze(repo)

    assert result["files"] == 1
    assert "app.py" in result["knowledge"]
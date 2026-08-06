from oae.core.repository_intelligence_builder import (
    RepositoryIntelligenceBuilder,
)


def test_builder_creation():
    builder = RepositoryIntelligenceBuilder()

    assert builder is not None


def test_builder_pipeline(tmp_path):
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

    builder = RepositoryIntelligenceBuilder()

    result = builder.build(repo)

    assert "files" in result
    assert "knowledge" in result
    assert "graph" in result
    assert len(result["files"]) == 1

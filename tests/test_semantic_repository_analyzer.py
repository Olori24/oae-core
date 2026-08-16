from oae.capabilities.semantic_repository_analyzer import (
    SemanticRepositoryAnalyzer,
)


def test_semantic_analysis(tmp_path):

    (tmp_path / "src").mkdir()

    analyzer = SemanticRepositoryAnalyzer()

    findings = analyzer.analyze(tmp_path)

    names = {
        finding[0]
        for finding in findings
    }

    assert "Logging" in names

    assert "Configuration" in names

    assert "Middleware" in names

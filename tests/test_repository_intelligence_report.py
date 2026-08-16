from oae.core.repository_intelligence_report import (
    RepositoryIntelligenceReport,
)


def test_generate():
    report = RepositoryIntelligenceReport()

    result = report.generate(".")

    assert "repository" in result
    assert "total_files" in result
    assert "python_files" in result


def test_directories():
    report = RepositoryIntelligenceReport()

    result = report.generate(".")

    assert result["source_directory_exists"] is True
    assert result["tests_directory_exists"] is True

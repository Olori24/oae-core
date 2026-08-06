from oae.core.repository_analyzer import RepositoryAnalyzer


def test_creation():
    analyzer = RepositoryAnalyzer()

    assert analyzer is not None


def test_empty_repository():
    analyzer = RepositoryAnalyzer()

    findings = analyzer.analyze([])

    assert findings == []


def test_none_repository():
    analyzer = RepositoryAnalyzer()

    findings = analyzer.analyze(None)

    assert findings == []


def test_single_item():
    analyzer = RepositoryAnalyzer()

    findings = analyzer.analyze(["auth.py"])

    assert len(findings) == 1
    assert findings[0] == "Review auth.py"


def test_multiple_items():
    analyzer = RepositoryAnalyzer()

    findings = analyzer.analyze([
        "auth.py",
        "models.py",
        "tests/",
    ])

    assert len(findings) == 3
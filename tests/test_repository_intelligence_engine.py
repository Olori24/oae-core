from oae.core.repository_intelligence_engine import (
    RepositoryIntelligenceEngine,
)


def test_creation():
    engine = RepositoryIntelligenceEngine()

    assert engine is not None


def test_empty():
    engine = RepositoryIntelligenceEngine()

    assert engine.classify([]) == []


def test_security_category():
    engine = RepositoryIntelligenceEngine()

    result = engine.classify(
        ["Security issue in auth.py"]
    )

    assert result[0]["category"] == "security"
    assert result[0]["priority"] == 10


def test_quality_category():
    engine = RepositoryIntelligenceEngine()

    result = engine.classify(
        ["Missing tests"]
    )

    assert result[0]["category"] == "quality"


def test_performance_category():
    engine = RepositoryIntelligenceEngine()

    result = engine.classify(
        ["Performance bottleneck"]
    )

    assert result[0]["category"] == "performance"


def test_architecture_category():
    engine = RepositoryIntelligenceEngine()

    result = engine.classify(
        ["Dependency cycle detected"]
    )

    assert result[0]["category"] == "architecture"


def test_general_category():
    engine = RepositoryIntelligenceEngine()

    result = engine.classify(
        ["Review README.md"]
    )

    assert result[0]["category"] == "general"
    assert result[0]["priority"] == 5
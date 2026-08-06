from oae.core.repository_diagnosis_engine import (
    RepositoryDiagnosisEngine,
)


GRAPH = {
    "auth.py": {
        "functions": ["login", "logout"],
        "classes": ["Auth"],
    },
    "models.py": {
        "functions": ["save"],
        "classes": ["User"],
    },
}


def test_creation():
    engine = RepositoryDiagnosisEngine()
    assert engine is not None


def test_file_count():
    engine = RepositoryDiagnosisEngine()

    result = engine.diagnose(GRAPH)

    assert result["files"] == 2


def test_function_count():
    engine = RepositoryDiagnosisEngine()

    result = engine.diagnose(GRAPH)

    assert result["functions"] == 3


def test_class_count():
    engine = RepositoryDiagnosisEngine()

    result = engine.diagnose(GRAPH)

    assert result["classes"] == 2


def test_health():
    engine = RepositoryDiagnosisEngine()

    result = engine.diagnose(GRAPH)

    assert result["health"] == "GOOD"
from oae.core.repository_diagnosis_v2 import RepositoryDiagnosisV2


INTELLIGENCE = {
    "knowledge": {
        "a.py": {
            "functions": ["a", "b"],
            "classes": ["A"],
        },
        "b.py": {
            "functions": ["c"],
            "classes": [],
        },
    }
}


def test_creation():
    engine = RepositoryDiagnosisV2()

    assert engine is not None


def test_diagnosis():
    engine = RepositoryDiagnosisV2()

    report = engine.diagnose(INTELLIGENCE)

    assert report["files"] == 2
    assert report["functions"] == 3
    assert report["classes"] == 1
    assert report["health"] == 100

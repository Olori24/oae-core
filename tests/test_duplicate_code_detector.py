from oae.core.duplicate_code_detector import (
    DuplicateCodeDetector,
)


def test_no_duplicates():
    detector = DuplicateCodeDetector()

    graph = {
        "a.py": {
            "functions": ["run"],
        },
        "b.py": {
            "functions": ["start"],
        },
    }

    assert detector.analyze(graph) == []


def test_duplicate_function():
    detector = DuplicateCodeDetector()

    graph = {
        "a.py": {
            "functions": ["run"],
        },
        "b.py": {
            "functions": ["run"],
        },
    }

    result = detector.analyze(graph)

    assert len(result) == 1
    assert result[0]["function"] == "run"
    assert result[0]["severity"] == "MEDIUM"


def test_multiple_duplicates():
    detector = DuplicateCodeDetector()

    graph = {
        "a.py": {
            "functions": ["run", "login"],
        },
        "b.py": {
            "functions": ["run", "login"],
        },
    }

    result = detector.analyze(graph)

    assert len(result) == 2

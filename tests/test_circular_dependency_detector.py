from oae.core.circular_dependency_detector import (
    CircularDependencyDetector,
)


def test_no_cycle():
    detector = CircularDependencyDetector()

    graph = {
        "a.py": {"imports": ["b.py"]},
        "b.py": {"imports": []},
    }

    assert detector.analyze(graph) == []


def test_simple_cycle():
    detector = CircularDependencyDetector()

    graph = {
        "a.py": {"imports": ["b.py"]},
        "b.py": {"imports": ["a.py"]},
    }

    result = detector.analyze(graph)

    assert len(result) == 1
    assert result[0]["severity"] == "HIGH"


def test_three_node_cycle():
    detector = CircularDependencyDetector()

    graph = {
        "a.py": {"imports": ["b.py"]},
        "b.py": {"imports": ["c.py"]},
        "c.py": {"imports": ["a.py"]},
    }

    result = detector.analyze(graph)

    assert len(result) == 1

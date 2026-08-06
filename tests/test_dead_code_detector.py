from oae.core.dead_code_detector import DeadCodeDetector


def test_empty_repository():
    detector = DeadCodeDetector()

    assert detector.analyze({}) == []


def test_empty_module():
    detector = DeadCodeDetector()

    graph = {
        "empty.py": {
            "functions": [],
            "classes": [],
            "imports": [],
        }
    }

    result = detector.analyze(graph)

    assert result[0]["type"] == "empty_module"


def test_import_only_module():
    detector = DeadCodeDetector()

    graph = {
        "config.py": {
            "functions": [],
            "classes": [],
            "imports": ["os"],
        }
    }

    result = detector.analyze(graph)

    assert result[0]["type"] == "imports_only"


def test_normal_module():
    detector = DeadCodeDetector()

    graph = {
        "app.py": {
            "functions": ["run"],
            "classes": ["App"],
            "imports": ["os"],
        }
    }

    result = detector.analyze(graph)

    assert result == []

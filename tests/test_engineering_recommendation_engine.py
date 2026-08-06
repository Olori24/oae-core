from oae.core.engineering_recommendation_engine import (
    EngineeringRecommendationEngine,
)


def test_empty_analysis():
    engine = EngineeringRecommendationEngine()

    assert engine.recommend({}) == []


def test_dead_code_recommendation():
    engine = EngineeringRecommendationEngine()

    analysis = {
        "dead_code": [
            {
                "type": "empty_module",
                "file": "legacy.py",
            }
        ]
    }

    result = engine.recommend(analysis)

    assert len(result) == 1
    assert result[0]["priority"] == "MEDIUM"
    assert result[0]["type"] == "remove_dead_code"


def test_duplicate_recommendation():
    engine = EngineeringRecommendationEngine()

    analysis = {
        "duplicates": [
            {
                "function": "run",
                "files": ["a.py", "b.py"],
            }
        ]
    }

    result = engine.recommend(analysis)

    assert len(result) == 1
    assert result[0]["priority"] == "LOW"
    assert result[0]["type"] == "merge_duplicate_code"


def test_circular_dependency_recommendation():
    engine = EngineeringRecommendationEngine()

    analysis = {
        "circular_dependencies": [
            {
                "cycle": [
                    "auth.py",
                    "security.py",
                    "auth.py",
                ]
            }
        ]
    }

    result = engine.recommend(analysis)

    assert len(result) == 1
    assert result[0]["priority"] == "HIGH"
    assert result[0]["type"] == "break_circular_dependency"


def test_priority_order():
    engine = EngineeringRecommendationEngine()

    analysis = {
        "duplicates": [
            {
                "function": "run",
                "files": ["a.py", "b.py"],
            }
        ],
        "dead_code": [
            {
                "type": "empty_module",
                "file": "legacy.py",
            }
        ],
        "circular_dependencies": [
            {
                "cycle": [
                    "a.py",
                    "b.py",
                    "a.py",
                ]
            }
        ],
    }

    result = engine.recommend(analysis)

    assert len(result) == 3
    assert result[0]["priority"] == "HIGH"
    assert result[1]["priority"] == "MEDIUM"
    assert result[2]["priority"] == "LOW"

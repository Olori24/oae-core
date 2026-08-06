from oae.core.intelligent_mission_generator import (
    IntelligentMissionGenerator,
)


def test_creation():
    generator = IntelligentMissionGenerator()

    assert generator is not None


def test_empty():
    generator = IntelligentMissionGenerator()

    assert generator.generate([]) == []


def test_security_agent():
    generator = IntelligentMissionGenerator()

    intelligence = [
        {
            "finding": "Security issue in auth.py",
            "category": "security",
            "priority": 10,
        }
    ]

    missions = generator.generate(intelligence)

    assert missions[0]["recommended_agent"] == "Security Engineer"


def test_quality_agent():
    generator = IntelligentMissionGenerator()

    intelligence = [
        {
            "finding": "Missing tests",
            "category": "quality",
            "priority": 6,
        }
    ]

    missions = generator.generate(intelligence)

    assert missions[0]["recommended_agent"] == "QA Engineer"


def test_architecture_agent():
    generator = IntelligentMissionGenerator()

    intelligence = [
        {
            "finding": "Dependency cycle",
            "category": "architecture",
            "priority": 8,
        }
    ]

    missions = generator.generate(intelligence)

    assert missions[0]["recommended_agent"] == "Architect Agent"


def test_title_generation():
    generator = IntelligentMissionGenerator()

    intelligence = [
        {
            "finding": "Dead code",
            "category": "general",
            "priority": 5,
        }
    ]

    missions = generator.generate(intelligence)

    assert missions[0]["title"] == "Resolve Dead code"


def test_priority_preserved():
    generator = IntelligentMissionGenerator()

    intelligence = [
        {
            "finding": "Performance bottleneck",
            "category": "performance",
            "priority": 8,
        }
    ]

    missions = generator.generate(intelligence)

    assert missions[0]["priority"] == 8
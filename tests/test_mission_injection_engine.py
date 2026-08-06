from oae.core.mission_injection_engine import (
    MissionInjectionEngine,
)


def test_empty_injection():
    engine = MissionInjectionEngine()

    result = engine.inject({"plans": []})

    assert result == []


def test_single_injection():
    engine = MissionInjectionEngine()

    recovery = {
        "plans": [
            {
                "mission": {
                    "type": "remove_dead_code",
                },
                "steps": [
                    "analyze",
                    "generate_patch",
                    "verify",
                    "execute",
                ],
            }
        ]
    }

    result = engine.inject(recovery)

    assert len(result) == 1
    assert result[0]["status"] == "pending"
    assert result[0]["mission"]["type"] == "remove_dead_code"


def test_multiple_injection():
    engine = MissionInjectionEngine()

    recovery = {
        "plans": [
            {
                "mission": {"type": "a"},
                "steps": [],
            },
            {
                "mission": {"type": "b"},
                "steps": [],
            },
        ]
    }

    result = engine.inject(recovery)

    assert len(result) == 2

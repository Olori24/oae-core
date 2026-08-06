from oae.core.autonomous_engineering_loop import (
    AutonomousEngineeringLoop,
)


def test_empty_loop():
    loop = AutonomousEngineeringLoop()

    result = loop.execute({"plans": []})

    assert result["missions"] == []
    assert result["queued"] == 0


def test_single_loop():
    loop = AutonomousEngineeringLoop()

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

    result = loop.execute(recovery)

    assert result["queued"] == 1
    assert len(result["missions"]) == 1


def test_multiple_loop():
    loop = AutonomousEngineeringLoop()

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

    result = loop.execute(recovery)

    assert result["queued"] == 2

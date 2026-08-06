from oae.core.repository_recovery_engine import (
    RepositoryRecoveryEngine,
)


def test_empty_recovery():
    engine = RepositoryRecoveryEngine()

    result = engine.recover([])

    assert result["plans"] == []
    assert result["patches"] == []
    assert result["verification"] == []


def test_single_recovery():
    engine = RepositoryRecoveryEngine()

    recommendations = [
        {
            "priority": "HIGH",
            "type": "break_circular_dependency",
        }
    ]

    result = engine.recover(recommendations)

    assert len(result["plans"]) == 1
    assert len(result["patches"]) == 1
    assert len(result["verification"]) == 1


def test_recovery_structure():
    engine = RepositoryRecoveryEngine()

    result = engine.recover([])

    assert "plans" in result
    assert "patches" in result
    assert "verification" in result

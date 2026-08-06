from oae.core.autonomous_repository_repair import (
    AutonomousRepositoryRepair,
)


def test_repair():
    repair = AutonomousRepositoryRepair()

    result = repair.repair(
        "print(1)\n",
        "print(2)\n",
    )

    assert result["status"] == "repaired"


def test_execution_exists():
    repair = AutonomousRepositoryRepair()

    result = repair.repair(
        "a\n",
        "b\n",
    )

    assert "execution" in result


def test_patch_generated():
    repair = AutonomousRepositoryRepair()

    result = repair.repair(
        "a\n",
        "b\n",
    )

    assert (
        result["execution"]["patch"]["status"]
        == "generated"
    )


def test_execution_completed():
    repair = AutonomousRepositoryRepair()

    result = repair.repair(
        "a\n",
        "b\n",
    )

    assert (
        result["execution"]["status"]
        == "completed"
    )

from oae.core.autonomous_repository_supervisor import (
    AutonomousRepositorySupervisor,
)


def test_creation():
    supervisor = AutonomousRepositorySupervisor()

    assert supervisor is not None


def test_empty_repository():
    supervisor = AutonomousRepositorySupervisor()

    assert supervisor.supervise([]) == []


def test_single_repository():
    supervisor = AutonomousRepositorySupervisor()

    supervisor.register("Backend Engineer")

    results = supervisor.supervise(["auth.py"])

    assert len(results) == 1


def test_multiple_repository():
    supervisor = AutonomousRepositorySupervisor()

    supervisor.register("Backend Engineer")

    results = supervisor.supervise([
        "auth.py",
        "models.py",
        "routes.py",
    ])

    assert len(results) == 3


def test_engineer_assignment():
    supervisor = AutonomousRepositorySupervisor()

    supervisor.register("Backend Engineer")

    results = supervisor.supervise(["auth.py"])

    assert results[0]["engineer"] == "Backend Engineer"
from oae.core.chief_architect_supervisor import (
    ChiefArchitectSupervisor,
)


def test_supervisor_creation():
    supervisor = ChiefArchitectSupervisor()

    assert supervisor is not None


def test_execute():
    supervisor = ChiefArchitectSupervisor()

    result = supervisor.execute(
        "Implement JWT Authentication"
    )

    assert result.completed is True


def test_execute_objective():
    supervisor = ChiefArchitectSupervisor()

    result = supervisor.execute(
        "Implement JWT Authentication"
    )

    assert result.mission == "Implement JWT Authentication"


def test_team_delegation():
    supervisor = ChiefArchitectSupervisor()

    supervisor.execute(
        "Implement JWT Authentication"
    )

    assert len(
        supervisor.collaboration.bus.messages
    ) == 4


def test_backend_receives_work():
    supervisor = ChiefArchitectSupervisor()

    supervisor.execute(
        "Implement JWT Authentication"
    )

    inbox = supervisor.collaboration.bus.inbox(
        "Backend Engineer"
    )

    assert len(inbox) == 1


def test_devops_receives_work():
    supervisor = ChiefArchitectSupervisor()

    supervisor.execute(
        "Implement JWT Authentication"
    )

    inbox = supervisor.collaboration.bus.inbox(
        "DevOps Engineer"
    )

    assert len(inbox) == 1
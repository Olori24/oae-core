from oae.core.execution_coordinator import ExecutionCoordinator


def test_coordinator_creation():
    coordinator = ExecutionCoordinator()

    assert coordinator is not None


def test_execute_without_matching_agent():
    coordinator = ExecutionCoordinator()

    result = coordinator.execute(
        "Implement JWT",
        "jwt",
    )

    assert result.assigned_agents == []


def test_execute_with_matching_agent():
    coordinator = ExecutionCoordinator()

    coordinator.register_agent(
        "Backend Engineer",
        ["python", "jwt", "fastapi"],
    )

    result = coordinator.execute(
        "Implement JWT",
        "jwt",
    )

    assert result.assigned_agents == [
        "Backend Engineer"
    ]


def test_scheduler_receives_task():
    coordinator = ExecutionCoordinator()

    coordinator.register_agent(
        "Backend Engineer",
        ["jwt"],
    )

    coordinator.execute(
        "Implement JWT",
        "jwt",
    )

    assert len(coordinator.scheduler.pending()) == 1


def test_correct_agent_selected():
    coordinator = ExecutionCoordinator()

    coordinator.register_agent(
        "Backend Engineer",
        ["python", "jwt"],
    )

    coordinator.register_agent(
        "Security Engineer",
        ["security"],
    )

    result = coordinator.execute(
        "Implement JWT",
        "jwt",
    )

    assert result.assigned_agents == [
        "Backend Engineer"
    ]
from oae.core.autonomous_executor import AutonomousExecutor


def test_execute_returns_result():
    executor = AutonomousExecutor()

    result = executor.execute("Add JWT authentication")

    assert result.objective == "Add JWT authentication"


def test_execution_completed():
    executor = AutonomousExecutor()

    result = executor.execute("Any task")

    assert result.completed is True


def test_tasks_completed():
    executor = AutonomousExecutor()

    result = executor.execute("Any task")

    assert result.tasks_completed == 9


def test_executor_creation():
    executor = AutonomousExecutor()

    assert executor is not None
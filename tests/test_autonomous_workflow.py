from oae.core.autonomous_workflow import AutonomousWorkflow


def test_workflow_creation():
    workflow = AutonomousWorkflow()

    assert workflow is not None


def test_workflow_execution():
    workflow = AutonomousWorkflow()

    result = workflow.run("Add JWT authentication")

    assert result.success is True


def test_workflow_objective():
    workflow = AutonomousWorkflow()

    result = workflow.run("Implement authentication")

    assert result.objective == "Implement authentication"


def test_multiple_runs():
    workflow = AutonomousWorkflow()

    first = workflow.run("Mission One")
    second = workflow.run("Mission Two")

    assert first.success is True
    assert second.success is True
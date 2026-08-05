from oae.core.architect_agent import ArchitectAgent


def test_architect_creation():
    agent = ArchitectAgent()

    assert agent is not None


def test_architecture_plan():
    agent = ArchitectAgent()

    plan = agent.design("Add JWT authentication")

    assert plan.objective == "Add JWT authentication"


def test_architecture_contains_language():
    agent = ArchitectAgent()

    plan = agent.design("Any task")

    assert isinstance(plan.language, str)


def test_architecture_contains_framework():
    agent = ArchitectAgent()

    plan = agent.design("Any task")

    assert isinstance(plan.framework, str)


def test_architecture_contains_tasks():
    agent = ArchitectAgent()

    plan = agent.design("Any task")

    assert len(plan.tasks) == 9
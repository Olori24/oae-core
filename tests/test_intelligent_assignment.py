from oae.core.intelligent_assignment import IntelligentAssignment


def test_creation():
    assignment = IntelligentAssignment()

    assert assignment is not None


def test_no_assignment():
    assignment = IntelligentAssignment()

    assert assignment.assignment() is None


def test_next_engineer():
    assignment = IntelligentAssignment()

    assignment.scheduler.workload.register("Backend Engineer")

    assert assignment.next_engineer() == "Backend Engineer"


def test_next_mission():
    assignment = IntelligentAssignment()

    assignment.scheduler.planner.planner.resolver.graph.add_mission(
        "Backend API"
    )

    assert assignment.next_missions() == ["Backend API"]


def test_assignment():
    assignment = IntelligentAssignment()

    assignment.scheduler.workload.register("Backend Engineer")

    assignment.scheduler.planner.planner.resolver.graph.add_mission(
        "Backend API"
    )

    result = assignment.assignment()

    assert result["mission"] == "Backend API"
    assert result["engineer"] == "Backend Engineer"
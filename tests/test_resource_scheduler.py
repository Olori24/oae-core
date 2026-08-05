from oae.core.resource_scheduler import ResourceScheduler


def test_scheduler_creation():
    scheduler = ResourceScheduler()

    assert scheduler is not None


def test_available_missions():
    scheduler = ResourceScheduler()

    scheduler.planner.planner.resolver.graph.add_mission(
        "Backend API"
    )

    missions = scheduler.available_missions()

    assert missions == ["Backend API"]


def test_least_busy_engineer():
    scheduler = ResourceScheduler()

    scheduler.workload.register("Backend Engineer")
    scheduler.workload.register("QA Engineer")

    scheduler.workload.assign("Backend Engineer")

    assert scheduler.least_busy_engineer() == "QA Engineer"


def test_no_engineers():
    scheduler = ResourceScheduler()

    assert scheduler.least_busy_engineer() is None


def test_multiple_missions():
    scheduler = ResourceScheduler()

    scheduler.planner.planner.resolver.graph.add_mission(
        "Backend API"
    )

    scheduler.planner.planner.resolver.graph.add_mission(
        "Documentation"
    )

    missions = scheduler.available_missions()

    assert len(missions) == 2
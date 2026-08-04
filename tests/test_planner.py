from oae.planner import Planner


def test_planner():

    planner = Planner()

    plan = planner.create_plan(
        "Build authentication"
    )

    assert plan.mission == "Build authentication"

    assert plan.profile is not None

    assert plan.profile.language == "Python"

    assert len(plan) == 6

    assert plan.tasks[0] == "Analyze mission"

    assert plan.tasks[-1] == "Verify results"

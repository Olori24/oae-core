from oae.core.autonomous_engineering_planner import (
    AutonomousEngineeringPlanner,
)


def test_empty_plan():
    planner = AutonomousEngineeringPlanner()

    result = planner.create_plan([])

    assert result == []


def test_single_recommendation():
    planner = AutonomousEngineeringPlanner()

    recommendations = [
        {
            "priority": "HIGH",
            "type": "break_circular_dependency",
        }
    ]

    plans = planner.create_plan(recommendations)

    assert len(plans) == 1
    assert plans[0]["mission"] == recommendations[0]
    assert plans[0]["steps"] == [
        "analyze",
        "generate_patch",
        "verify",
        "execute",
    ]


def test_multiple_recommendations():
    planner = AutonomousEngineeringPlanner()

    recommendations = [
        {
            "priority": "HIGH",
            "type": "break_circular_dependency",
        },
        {
            "priority": "MEDIUM",
            "type": "remove_dead_code",
        },
        {
            "priority": "LOW",
            "type": "merge_duplicate_code",
        },
    ]

    plans = planner.create_plan(recommendations)

    assert len(plans) == 3

    for plan in plans:
        assert "mission" in plan
        assert "steps" in plan
        assert len(plan["steps"]) == 4


def test_plan_step_order():
    planner = AutonomousEngineeringPlanner()

    recommendation = [
        {
            "priority": "HIGH",
            "type": "break_circular_dependency",
        }
    ]

    plan = planner.create_plan(recommendation)[0]

    assert plan["steps"][0] == "analyze"
    assert plan["steps"][1] == "generate_patch"
    assert plan["steps"][2] == "verify"
    assert plan["steps"][3] == "execute"

from oae.core.autonomous_agent import next_agent_decision
from oae.core.engineering_planner import build_engineering_plan


def test_plan_has_bounded_reviewed_lifecycle():
    plan = build_engineering_plan(
        objective="add tenant-safe repository health reporting",
        repository_kind="python",
        has_tests=True,
        has_linter=True,
        has_typecheck=True,
    )
    assert plan.version == "1.0"
    actions = [step.action for step in plan.steps]
    assert actions[0] == "analyze_repository"
    assert actions[-1] == "create_pull_request"
    assert "verify_workspace" in actions
    assert len(plan.steps) <= 16


def test_agent_respects_dependencies():
    plan = build_engineering_plan(objective="fix a failing API test", repository_kind="python").to_dict()
    decision = next_agent_decision(plan, ["inspect", "baseline", "implement", "diff"])
    assert decision.status == "ready"
    assert decision.action == "verify_workspace"


def test_agent_rejects_unknown_action():
    plan = {"steps": [{"id": "x", "action": "run_shell", "requires": []}]}
    try:
        next_agent_decision(plan, [])
    except ValueError:
        return
    raise AssertionError("unsafe action was accepted")

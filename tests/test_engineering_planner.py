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
    assert any(step.optional for step in plan.steps if step.id == "repair")


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


def test_failed_verification_opens_repair_path():
    plan = build_engineering_plan(objective="repair an API regression", repository_kind="python").to_dict()
    decision = next_agent_decision(plan, ["inspect", "baseline", "implement", "diff", "verify", "verify_failed"])
    assert decision.action == "repair_failures"


def test_plan_preserves_bounded_action_inputs():
    plan = build_engineering_plan(
        objective="update the health endpoint",
        repository_kind="python",
        action_inputs={
            "implement": {
                "mutation": {
                    "type": "write",
                    "path": "src/app.py",
                    "content": "print('ok')\n",
                }
            }
        },
    )
    implement = next(step for step in plan.steps if step.id == "implement")
    assert implement.inputs["mutation"]["type"] == "write"


def test_greenfield_plan_stops_at_verified_workspace():
    plan = build_engineering_plan(
        objective="build a school management system",
        repository_kind="python",
        has_tests=True,
        has_linter=True,
        greenfield=True,
    )
    actions = [step.action for step in plan.steps]
    assert actions[:2] == ["capture_baseline", "code_objective"]
    assert "verify_workspace" in actions
    assert "create_pull_request" not in actions
    assert "sync_github" not in actions

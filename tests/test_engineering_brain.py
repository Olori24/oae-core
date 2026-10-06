from oae.core.agent_runtime import record_step_result, start_agent_run
from oae.core.engineering_planner import build_engineering_plan


def test_engineering_plan_is_bounded_and_verifiable():
    plan = build_engineering_plan(
        objective="Fix authentication and add regression coverage.",
        repository_kind="python",
        has_tests=True,
        has_linter=True,
        has_typecheck=True,
        security_required=True,
    )
    payload = plan.to_dict()
    assert len(payload["steps"]) <= 32
    assert payload["verification_commands"] == ["python_compile", "ruff", "mypy", "pytest"]
    assert payload["steps"][0]["action"] == "analyze_repository"
    assert payload["steps"][-1]["action"] == "create_pull_request"


def test_failed_verification_enters_bounded_repair_then_reverify():
    plan = build_engineering_plan(
        objective="Fix a regression.",
        repository_kind="python",
        has_tests=True,
    ).to_dict()
    state = start_agent_run(run_id="run-1", plan=plan, max_repairs=1)

    for step_id in ("inspect", "baseline", "implement", "diff"):
        state = record_step_result(state, step_id=step_id, success=True)

    state = record_step_result(
        state, step_id="verify", success=False, evidence={"failure": "test failed"}
    )
    assert state.status == "running"
    assert state.failed_step == "verify"
    assert state.repair_count == 1
    assert "verify_failed" in state.completed_steps

    state = record_step_result(
        state, step_id="repair", success=True, evidence={"repair": "minimal fix"}
    )
    state = record_step_result(state, step_id="reverify", success=True)
    assert state.status == "running"
    assert "reverify" in state.completed_steps


def test_agent_run_never_allows_unsupported_plan_actions():
    plan = build_engineering_plan(objective="Inspect repository").to_dict()
    plan["steps"][0]["action"] = "run_unrestricted_shell"
    state = start_agent_run(run_id="run-2", plan=plan)
    try:
        state.next_decision()
    except ValueError as exc:
        assert "unsupported agent action" in str(exc)
    else:
        raise AssertionError("unsupported action was accepted")

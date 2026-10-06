from oae.core.agent_runtime import record_step_result, start_agent_run


def _plan():
    return {
        "max_repairs": 2,
        "steps": [
            {"id": "inspect", "action": "analyze_repository", "requires": []},
            {"id": "verify", "action": "verify_workspace", "requires": ["inspect"]},
            {
                "id": "repair",
                "action": "repair_failures",
                "requires": ["verify"],
                "optional": True,
            },
            {
                "id": "reverify",
                "action": "verify_workspace",
                "requires": ["repair"],
                "optional": True,
            },
        ],
    }


def test_successful_steps_are_idempotent():
    state = start_agent_run(run_id="r1", plan=_plan())
    state = record_step_result(state, step_id="inspect", success=True, evidence={"ok": True})
    again = record_step_result(state, step_id="inspect", success=True, evidence={"ok": True})
    assert again == state
    assert state.next_decision().action == "verify_workspace"


def test_failed_verification_opens_bounded_repair_path():
    state = start_agent_run(run_id="r2", plan=_plan())
    state = record_step_result(state, step_id="inspect", success=True)
    state = record_step_result(state, step_id="verify", success=False, evidence={"failed": ["pytest"]})
    assert state.status == "running"
    assert state.failed_step == "verify"
    assert state.repair_count == 1
    assert "verify_failed" in state.completed_steps
    assert state.next_decision().action == "repair_failures"


def test_repair_budget_is_fail_closed():
    plan = {**_plan(), "max_repairs": 0}
    state = start_agent_run(run_id="r3", plan=plan, max_repairs=0)
    state = record_step_result(state, step_id="inspect", success=True)
    state = record_step_result(state, step_id="verify", success=False)
    assert state.status == "failed"
    assert state.repair_count == 0


def test_reverification_failure_reopens_bounded_repair_path():
    state = start_agent_run(run_id="r4", plan=_plan())
    state = record_step_result(state, step_id="inspect", success=True)
    state = record_step_result(state, step_id="verify", success=False)
    state = record_step_result(state, step_id="repair", success=True)
    state = record_step_result(state, step_id="reverify", success=False)
    assert state.status == "running"
    assert state.repair_count == 2
    assert "repair" not in state.completed_steps
    assert state.next_decision().action == "repair_failures"

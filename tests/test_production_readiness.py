from oae.core.production_readiness import evaluate_production_readiness


def test_production_gate_is_fail_closed():
    result = evaluate_production_readiness(
        quality_verified=True, workspace_verified=True, ci_status="passed",
        change_set_synced=True, pull_request_open=True,
    )
    assert result["verified"] is False
    assert "deployment_verified" in result["blockers"]


def test_production_gate_passes_only_with_all_evidence():
    result = evaluate_production_readiness(
        quality_verified=True, workspace_verified=True, ci_status="passed",
        change_set_synced=True, pull_request_open=True,
        deployment_verified=True, rollback_verified=True,
    )
    assert result["verified"] is True
    assert result["status"] == "ready"

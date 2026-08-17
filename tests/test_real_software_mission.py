from examples.real_software_mission import MISSION, run


def test_real_software_mission_produces_verified_candidate(tmp_path):
    result = run(tmp_path / "teampulse")

    assert result["application"] == "TeamPulse"
    assert result["status"] == "production_candidate"
    assert result["readiness_score"] == 100
    assert result["verified"] is True
    assert result["blockers"] == []

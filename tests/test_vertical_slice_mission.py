from oae.core.vertical_slice_mission import VerticalSliceMission


def test_product_specification_enters_vertical_slice_pipeline(tmp_path):
    result = VerticalSliceMission().run(
        tmp_path / "team-pulse",
        name="TeamPulse",
        description="A developer workspace for tracking engineering jobs and results.",
    )

    assert result["mission"] == "TeamPulse"
    assert result["status"] in {"production_candidate", "blocked"}
    assert "blockers" in result
    assert "contract" in result

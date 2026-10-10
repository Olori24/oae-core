"""End-to-end acceptance test for OAE's greenfield project-builder milestone.

This intentionally runs the real scaffold, contract checks, backend execution, and
frontend production build. A generated project must earn the verified status; merely
creating the expected files is not enough.
"""
import json
import shutil

import pytest

from oae.core.vertical_slice_mission import VerticalSliceMission


@pytest.mark.skipif(shutil.which("npm") is None, reason="end-to-end builder gate requires npm")
def test_greenfield_project_builder_generates_and_verifies_a_real_app(tmp_path):
    result = VerticalSliceMission().run(
        tmp_path / "clinic-booking",
        name="Clinic Booking",
        description=(
            "Build a small appointment booking application with patient records, "
            "appointment creation, a health endpoint, and a simple web interface."
        ),
        language="Python",
        framework="FastAPI",
        database="SQLite",
        testing_framework="pytest",
    )

    assert result["root"] == str(tmp_path / "clinic-booking")
    assert result["contract"]["passed"] is True
    assert result["verification"] is not None
    assert result["verified"] is True, json.dumps(result, indent=2)
    assert result["status"] == "production_candidate"
    assert result["blockers"] == []

    checks = result["verification"]["checks"]
    assert checks, "The verifier must return actual check evidence."
    assert all(check["passed"] for check in checks), json.dumps(checks, indent=2)
    assert (tmp_path / "clinic-booking" / "src" / "main.py").is_file()
    assert (tmp_path / "clinic-booking" / "web" / "app" / "page.tsx").is_file()

from pathlib import Path

import pytest

from benchmarks.greenfield_project_builder import run_benchmark


class FakeMission:
    def __init__(self, result):
        self.result = result

    def run(self, root, **kwargs):
        (Path(root) / "README.md").write_text("# Demo\n", encoding="utf-8")
        return self.result


def test_benchmark_records_verified_project_evidence(tmp_path):
    result = run_benchmark(
        tmp_path / "empty-project",
        name="Demo",
        description="A demo project",
        mission=FakeMission(
            {
                "status": "production_candidate",
                "verified": True,
                "readiness_score": 100,
                "blockers": [],
                "contract": {"passed": True},
                "verification": {
                    "status": "verified",
                    "checks": [{"name": "pytest", "passed": True, "detail": "passed"}],
                },
            }
        ),
    )

    assert result["benchmark"] == "oae-greenfield-project-builder-v1"
    assert result["result"]["verified"] is True
    assert result["result"]["file_count"] == 1
    assert result["acceptance"]["all_declared_checks_passed"] is True
    assert result["limitations"]


def test_benchmark_does_not_mark_blocked_project_as_verified(tmp_path):
    result = run_benchmark(
        tmp_path / "blocked-project",
        mission=FakeMission(
            {
                "status": "blocked",
                "verified": False,
                "readiness_score": 40,
                "blockers": ["frontend build"],
                "contract": {"passed": True},
                "verification": {
                    "status": "failed",
                    "checks": [{"name": "frontend build", "passed": False, "detail": "exit 1"}],
                },
            }
        ),
    )

    assert result["result"]["verified"] is False
    assert result["result"]["failed_checks"][0]["name"] == "frontend build"
    assert result["acceptance"]["verification_passed"] is False


def test_benchmark_requires_an_empty_workspace(tmp_path):
    root = tmp_path / "not-empty"
    root.mkdir()
    (root / "existing.txt").write_text("do not overwrite", encoding="utf-8")

    with pytest.raises(ValueError, match="must be empty"):
        run_benchmark(root, mission=FakeMission({}))

def test_benchmark_fails_closed_when_verification_evidence_is_missing(tmp_path):
    result = run_benchmark(
        tmp_path / "missing-evidence",
        mission=FakeMission(
            {
                "status": "production_candidate",
                "verified": True,
                "readiness_score": 100,
                "blockers": [],
                "contract": {"passed": True},
                "verification": None,
            }
        ),
    )

    assert result["result"]["verified"] is True
    assert result["acceptance"]["verification_passed"] is False
    assert result["acceptance"]["all_declared_checks_passed"] is False

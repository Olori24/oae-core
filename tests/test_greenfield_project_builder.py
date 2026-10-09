import pytest
from pydantic import ValidationError

import oae.api.job_runner as job_runner_module
import oae.api.workspace_manager as workspace_manager_module
from oae.api.engineering_routes import GreenfieldProjectRequest
from oae.api.job_runner import JobRunner
from oae.api.workspace_manager import WorkspaceManager


class FakeRepository:
    def __init__(self):
        self.reservations = []
        self.ready = []
        self.failed = []

    def reserve(self, record, entries):
        self.reservations.append((record, entries))

    def mark_ready(self, tenant_id, workspace_id, ready_at):
        self.ready.append((tenant_id, workspace_id, ready_at))

    def mark_failed(self, tenant_id, workspace_id, failure_code):
        self.failed.append((tenant_id, workspace_id, failure_code))


class FakeMission:
    def __init__(self, result):
        self.result = result

    def run(self, root, **kwargs):
        root.mkdir(parents=True, exist_ok=True)
        (root / "README.md").write_text("# generated project\n", encoding="utf-8")
        return self.result


def test_greenfield_workspace_preserves_mission_verification_evidence(tmp_path, monkeypatch):
    mission_result = {
        "mission": "demo",
        "status": "ready",
        "verified": True,
        "readiness_score": 100,
        "blockers": [],
        "root": str(tmp_path),
        "contract": {"passed": True},
        "verification": {"passed": True},
    }
    monkeypatch.setattr(
        workspace_manager_module,
        "VerticalSliceMission",
        lambda: FakeMission(mission_result),
    )
    manager = WorkspaceManager(root=tmp_path, repository=FakeRepository())

    record, manifest, result = manager.provision_greenfield_with_result(
        "tenant-1",
        name="Demo",
        description="A small demo project",
    )

    assert record.state.value == "ready"
    assert record.repository_id is None
    assert result == mission_result
    assert "README.md" in {entry.relative_path for entry in manifest.entries}


def test_greenfield_request_rejects_unapproved_stack_values():
    with pytest.raises(ValidationError):
        GreenfieldProjectRequest(
            name="Demo",
            description="A small demo project",
            language="Bash",
            authorization_id="auth-1",
        )


def test_greenfield_job_does_not_claim_verification_when_gate_is_blocked(monkeypatch):
    class Record:
        def model_dump(self, mode="json"):
            return {"id": "workspace-1", "state": "ready"}

    class Manifest:
        def model_dump(self, mode="json"):
            return {"workspace_id": "workspace-1", "entries": []}

    class Manager:
        def provision_greenfield_with_result(self, tenant_id, **kwargs):
            assert tenant_id == "tenant-1"
            return Record(), Manifest(), {
                "status": "blocked",
                "verified": False,
                "blockers": ["tests"],
            }

    monkeypatch.setattr(job_runner_module, "WorkspaceManager", Manager)
    result = JobRunner._provision_greenfield_workspace(
        {"name": "Demo", "description": "A demo", "stage": "greenfield_provision"},
        "tenant-1",
    )

    assert result["evidence"]["verified"] is False
    assert result["evidence"]["mission"]["blockers"] == ["tests"]
    assert "did not pass" in result["summary"]

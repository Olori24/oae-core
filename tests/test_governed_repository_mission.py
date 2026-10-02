from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

from oae.api.job_runner import JobRunner
from oae.api.workspace_models import WorkspacePurpose, WorkspaceRecord, WorkspaceState


def _record(tmp_path: Path) -> WorkspaceRecord:
    now = datetime.now(timezone.utc)
    return WorkspaceRecord(
        id="workspace-1",
        tenant_id="tenant-1",
        repository_id="repo-1",
        source_revision_id="rev-1",
        purpose=WorkspacePurpose.EXECUTION,
        state=WorkspaceState.READY,
        storage_uri=(tmp_path / "workspace").as_uri(),
        manifest_uri=(tmp_path / "workspace" / "manifest.json").as_uri(),
        manifest_sha256="0" * 64,
        size_bytes=1,
        file_count=1,
        retention_expires_at=now + timedelta(days=1),
        created_at=now,
        ready_at=now,
    )


def test_repository_mission_requires_matching_durable_authorization(monkeypatch, tmp_path):
    class FakeAuthRepo:
        def get(self, **_kwargs):
            return SimpleNamespace(
                status="approved",
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
                operation="repository_mission",
                scope={"repository_id": "other-repo", "revision_id": "rev-1", "allowed_operations": "create_file"},
            )

    monkeypatch.setattr("oae.api.job_runner.WorkerAuthorizationRepository", FakeAuthRepo)

    try:
        JobRunner()._dispatch(
            "repository_mission",
            {
                "repository_id": "repo-1",
                "revision_id": "rev-1",
                "actions": [{"operation": "create_file", "path": "app.py", "content": "print(1)"}],
            },
            "job-1",
            tenant_id="tenant-1",
            authorization_id="auth-1",
        )
    except PermissionError as exc:
        assert "scope" in str(exc)
    else:
        raise AssertionError("mismatched authorization scope was accepted")


def test_repository_mission_provisions_execution_workspace_and_executes_only_authorized_actions(
    monkeypatch, tmp_path
):
    workspace = _record(tmp_path)

    class FakeAuthRepo:
        def get(self, **_kwargs):
            return SimpleNamespace(
                status="approved",
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
                operation="repository_mission",
                scope={
                    "repository_id": "repo-1",
                    "revision_id": "rev-1",
                    "allowed_operations": "create_file,create_branch,commit_changes",
                },
            )

    class FakeWorkspaceManager:
        def provision(self, **kwargs):
            assert kwargs["tenant_id"] == "tenant-1"
            assert kwargs["repository_id"] == "repo-1"
            assert kwargs["revision_id"] == "rev-1"
            assert kwargs["purpose"] is WorkspacePurpose.EXECUTION
            (tmp_path / "workspace").mkdir()
            return workspace, None

    captured = {}

    class FakeExecutor:
        def __init__(self, security):
            captured["security"] = security

        def execute(self, actions, workspace_path):
            captured["actions"] = actions
            captured["workspace_path"] = workspace_path
            return [
                {"operation": action["operation"], "status": "completed", "result": {"ok": True}}
                for action in actions
            ]

    monkeypatch.setattr("oae.api.job_runner.WorkerAuthorizationRepository", FakeAuthRepo)
    monkeypatch.setattr("oae.api.job_runner.WorkspaceManager", FakeWorkspaceManager)
    monkeypatch.setattr("oae.api.job_runner.EngineeringActionExecutor", FakeExecutor)

    result = JobRunner()._dispatch(
        "repository_mission",
        {
            "repository_id": "repo-1",
            "revision_id": "rev-1",
            "commit_message": "test mission",
            "actions": [
                {"operation": "create_file", "path": "app.py", "content": "print(1)", "workspace_path": "/escape"},
                {"operation": "commit_changes", "workspace_path": "/escape"},
            ],
        },
        "job-1",
        tenant_id="tenant-1",
        authorization_id="auth-1",
    )

    assert result["operation"] == "repository_mission"
    assert captured["workspace_path"] == Path(workspace.storage_uri.removeprefix("file://"))
    assert all("workspace_path" not in action for action in captured["actions"])
    assert captured["actions"][1]["message"] == "test mission"
    assert captured["security"].permissions.allowed("write_repository")
    assert captured["security"].permissions.allowed("commit_changes")

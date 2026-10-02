from pathlib import Path

from oae.core.process_security import run_git
from oae.core.repository_execution_engine import RepositoryExecutionEngine
from oae.security.kernel import SecurityKernel


def _git_repo(tmp_path: Path) -> Path:
    run_git(["init", "-b", "main"], cwd=tmp_path, check=True)
    run_git(["config", "user.name", "OAE Test"], cwd=tmp_path, check=True)
    run_git(["config", "user.email", "oae-test@example.invalid"], cwd=tmp_path, check=True)
    (tmp_path / "app.py").write_text("value = 1\n", encoding="utf-8")
    run_git(["add", "--", "app.py"], cwd=tmp_path, check=True)
    run_git(["commit", "-m", "initial"], cwd=tmp_path, check=True)
    return tmp_path


def _authorized_engine() -> RepositoryExecutionEngine:
    security = SecurityKernel()
    security.permissions.allow("write_repository")
    security.permissions.allow("commit_changes")
    security.approvals.approve("write_repository")
    security.approvals.approve("commit_changes")
    return RepositoryExecutionEngine(security=security)


def test_real_branch_and_commit_require_governance(tmp_path):
    workspace = _git_repo(tmp_path)
    engine = RepositoryExecutionEngine()

    denied = engine.execute_operation(
        {"operation": "create_branch", "branch": "oae/test", "workspace_path": workspace}
    )
    assert denied["status"] == "denied"

    denied_commit = engine.execute_operation(
        {
            "operation": "commit_changes",
            "message": "should be denied",
            "workspace_path": workspace,
        }
    )
    assert denied_commit["status"] == "denied"


def test_real_branch_commit_and_test_are_bounded(tmp_path):
    workspace = _git_repo(tmp_path)
    engine = _authorized_engine()

    branch = engine.execute_operation(
        {"operation": "create_branch", "branch": "oae/test", "workspace_path": workspace}
    )
    assert branch["status"] == "completed"
    assert branch["result"]["branch"] == "oae/test"

    changed = engine.execute_operation(
        {
            "operation": "modify_file",
            "path": "app.py",
            "content": "value = 2\n",
            "workspace_path": workspace,
        }
    )
    assert changed["status"] == "completed"

    committed = engine.execute_operation(
        {
            "operation": "commit_changes",
            "message": "feat: bounded engineering change",
            "workspace_path": workspace,
            "paths": ["app.py"],
        }
    )
    assert committed["status"] == "completed"
    assert len(committed["result"]["commit_sha"]) == 40

    tested = engine.execute_operation(
        {
            "operation": "run_tests",
            "command": ["python", "--version"],
            "workspace_path": workspace,
        }
    )
    assert tested["result"]["passed"] is True

    assert engine.branch_manager.current_branch(workspace) == "oae/test"
    log = run_git(["log", "-1", "--format=%s"], cwd=workspace, check=True)
    assert log.stdout.strip() == "feat: bounded engineering change"

from oae.core.repository_execution_engine import RepositoryExecutionEngine
from oae.security.kernel import SecurityKernel


def _authorized_engine():
    security = SecurityKernel()
    security.permissions.allow("write_repository")
    security.approvals.approve("write_repository")
    return RepositoryExecutionEngine(security=security)


def test_execute_operations_persists_change_in_one_workspace(tmp_path):
    (tmp_path / "app.py").write_text("value = 1\n", encoding="utf-8")

    engine = _authorized_engine()
    results = engine.execute_operations(
        [
            {"operation": "modify_file", "path": "app.py", "content": "value = 2\n"},
            {"operation": "run_tests", "command": ["pytest", "-q", "test_smoke.py"]},
        ],
        tmp_path,
    )

    assert results[0]["status"] == "completed"
    assert (tmp_path / "app.py").read_text(encoding="utf-8") == "value = 2\n"


def test_execute_operations_rejects_workspace_escape(tmp_path):
    engine = _authorized_engine()

    result = engine.execute_operation(
        {
            "operation": "create_file",
            "path": "../outside.txt",
            "content": "must not escape",
            "workspace_path": str(tmp_path),
        }
    )

    assert result["status"] == "denied"
    assert not (tmp_path.parent / "outside.txt").exists()


def test_modify_file_requires_existing_target(tmp_path):
    engine = _authorized_engine()

    result = engine.execute_operation(
        {
            "operation": "modify_file",
            "path": "missing.py",
            "content": "value = 1\n",
            "workspace_path": str(tmp_path),
        }
    )

    assert result["status"] == "error"
    assert "does not exist" in result["error"]

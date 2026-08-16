from pathlib import Path

from oae.agents.engineering_action_executor import EngineeringActionExecutor
from oae.security.kernel import SecurityKernel


def authorized_executor():
    security = SecurityKernel()
    security.permissions.allow("write_repository")
    security.approvals.approve("write_repository")
    return EngineeringActionExecutor(security=security)


def test_execute_actions():
    executor = EngineeringActionExecutor()
    actions = [
        {"action": "analyze", "target": "Implement Logging"},
        {"action": "implement", "target": "Implement Logging"},
        {"action": "verify", "target": "Implement Logging"},
    ]
    results = executor.execute(actions)
    assert len(results) == 3
    assert [r["status"] for r in results] == ["completed"] * 3
    assert [r["action"] for r in results] == ["analyze", "implement", "verify"]


def test_repository_write_requires_authorization():
    executor = EngineeringActionExecutor()
    result = executor.execute([{
        "operation": "modify_file",
        "path": "README.md",
        "content": "denied\n",
    }])[0]
    assert result["status"] == "denied"


def test_execute_repository_operation():
    executor = authorized_executor()
    results = executor.execute([{
        "operation": "modify_file",
        "path": "README.md",
        "content": "OAE autonomous engineering test\n",
    }])
    assert results[0]["status"] == "completed"
    workspace = results[0]["workspace"]
    assert workspace["created"] is True
    assert (Path(workspace["path"]) / "README.md").read_text(encoding="utf-8") == "OAE autonomous engineering test\n"


def test_create_file_operation():
    executor = authorized_executor()
    results = executor.execute([{
        "operation": "create_file",
        "path": "src/generated/hello.py",
        "content": "print('hello from OAE')\n",
    }])
    assert results[0]["status"] == "completed"
    workspace = results[0]["workspace"]
    file_path = Path(workspace["path"]) / "src/generated/hello.py"
    assert file_path.exists()
    assert file_path.read_text(encoding="utf-8") == "print('hello from OAE')\n"


def test_run_tests_operation():
    executor = EngineeringActionExecutor()
    results = executor.execute([{
        "operation": "run_tests",
        "command": ["python", "-c", "print('OAE TEST PASS')"],
    }])
    assert results[0]["status"] == "completed"
    assert results[0]["result"]["returncode"] == 0
    assert results[0]["result"]["passed"] is True
    assert "OAE TEST PASS" in results[0]["result"]["stdout"]

from pathlib import Path

from oae.agents.engineering_action_executor import (
    EngineeringActionExecutor,
)


def test_execute_actions():

    executor = EngineeringActionExecutor()

    actions = [
        {
            "action": "analyze",
            "target": "Implement Logging",
        },
        {
            "action": "implement",
            "target": "Implement Logging",
        },
        {
            "action": "verify",
            "target": "Implement Logging",
        },
    ]

    results = executor.execute(actions)

    assert len(results) == 3

    assert results[0]["status"] == "completed"
    assert results[1]["status"] == "completed"
    assert results[2]["status"] == "completed"

    assert results[0]["action"] == "analyze"
    assert results[1]["action"] == "implement"
    assert results[2]["action"] == "verify"


def test_execute_repository_operation():

    executor = EngineeringActionExecutor()

    actions = [
        {
            "operation": "modify_file",
            "path": "README.md",
            "content": "OAE autonomous engineering test\n",
        }
    ]

    results = executor.execute(actions)

    assert len(results) == 1
    assert results[0]["operation"] == "modify_file"
    assert results[0]["path"] == "README.md"
    assert results[0]["status"] == "completed"

    workspace = results[0]["workspace"]

    assert workspace["created"] is True

    file_path = (
        Path(workspace["path"]) / "README.md"
    )

    assert file_path.exists()

    assert file_path.read_text(
        encoding="utf-8"
    ) == "OAE autonomous engineering test\n"


def test_create_file_operation():

    executor = EngineeringActionExecutor()

    actions = [
        {
            "operation": "create_file",
            "path": "src/generated/hello.py",
            "content": "print('hello from OAE')\n",
        }
    ]

    results = executor.execute(actions)

    assert len(results) == 1

    assert results[0]["operation"] == "create_file"
    assert results[0]["path"] == "src/generated/hello.py"
    assert results[0]["status"] == "completed"

    workspace = results[0]["workspace"]

    assert workspace["created"] is True

    file_path = (
        Path(workspace["path"])
        / "src/generated/hello.py"
    )

    assert file_path.exists()

    assert file_path.read_text(
        encoding="utf-8"
    ) == "print('hello from OAE')\n"
def test_run_tests_operation():

    executor = EngineeringActionExecutor()

    actions = [
        {
            "operation": "run_tests",
            "command": [
                "python",
                "-c",
                "print('OAE TEST PASS')",
            ],
        }
    ]

    results = executor.execute(actions)

    assert len(results) == 1

    assert results[0]["operation"] == "run_tests"

    assert results[0]["status"] == "completed"

    test_result = results[0]["result"]

    assert test_result["returncode"] == 0

    assert test_result["passed"] is True

    assert "OAE TEST PASS" in test_result["stdout"]

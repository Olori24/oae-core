from oae.core.repository_sandbox_execution_engine import (
    RepositorySandboxExecutionEngine,
)


def test_execute_patch():
    engine = RepositorySandboxExecutionEngine()

    result = engine.execute({})

    assert result["success"] is True
    assert result["sandbox"] == "sandbox-001"


def test_structure():
    engine = RepositorySandboxExecutionEngine()

    result = engine.execute({})

    assert "success" in result
    assert "sandbox" in result
    assert "patch" in result

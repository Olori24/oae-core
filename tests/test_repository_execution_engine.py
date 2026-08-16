from oae.core.repository_execution_engine import (
    RepositoryExecutionEngine,
)


def test_execute():
    engine = RepositoryExecutionEngine()

    result = engine.execute(
        "print(1)\n",
        "print(2)\n",
    )

    assert result["status"] == "completed"


def test_workspace_created():
    engine = RepositoryExecutionEngine()

    result = engine.execute(
        "a\n",
        "b\n",
    )

    assert result["workspace"]["created"] is True


def test_branch_created():
    engine = RepositoryExecutionEngine()

    result = engine.execute(
        "a\n",
        "b\n",
    )

    assert result["branch"]["status"] == "created"


def test_patch_generated():
    engine = RepositoryExecutionEngine()

    result = engine.execute(
        "a\n",
        "b\n",
    )

    assert result["patch"]["status"] == "generated"

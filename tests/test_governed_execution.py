from pathlib import Path

import pytest

from oae.core.governed_execution import command_spec, run_governed_command
from oae.core.process_security import ProcessPolicyError


def test_only_allowlisted_commands_are_resolvable():
    assert command_spec("pytest").name == "pytest"
    with pytest.raises(ProcessPolicyError):
        command_spec("bash")


def test_python_compile_runs_without_shell(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "example.py").write_text("value = 1\n", encoding="utf-8")
    result = run_governed_command("python_compile", workspace=tmp_path)
    assert result["passed"] is True
    assert result["exit_code"] == 0


def test_command_output_is_bounded():
    spec = command_spec("pytest")
    assert spec.timeout_seconds <= 600
    assert spec.max_output_bytes <= 200_000


def test_node_profiles_require_workspace_local_tools(tmp_path: Path):
    assert command_spec("typescript_check").local_only is True
    assert command_spec("eslint_check").local_only is True
    assert command_spec("vitest_check").local_only is True
    assert command_spec("jest_check").local_only is True

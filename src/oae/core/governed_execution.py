"""Governed repository command execution.

Commands are selected by OAE, never supplied as an arbitrary shell string.
No shell is used. Output and runtime are bounded. The runner executes only
against an approved workspace.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from oae.core.process_security import (
    ProcessPolicyError,
    ProcessTimeout,
    resolve_workspace_executable,
    run_absolute_command,
)


class CommandExecutionError(RuntimeError):
    """Raised when a governed command cannot be executed safely."""


@dataclass(frozen=True)
class CommandSpec:
    name: str
    executable: str
    args: tuple[str, ...]
    timeout_seconds: int = 300
    max_output_bytes: int = 200_000


_COMMANDS: dict[str, CommandSpec] = {
    "pytest": CommandSpec("pytest", "pytest", ("-q",), 600),
    "ruff": CommandSpec("ruff", "ruff", ("check", "."), 300),
    "mypy": CommandSpec("mypy", "mypy", ("src",), 300),
    "python_compile": CommandSpec("python_compile", "python", ("-m", "compileall", "-q", "src"), 180),
    "typescript_check": CommandSpec("typescript_check", "tsc", ("--noEmit",), 600),
}


def command_spec(name: str) -> CommandSpec:
    try:
        return _COMMANDS[name]
    except KeyError as exc:
        raise ProcessPolicyError("Requested engineering command is not allowlisted.") from exc


def run_governed_command(name: str, *, workspace: str | Path) -> dict:
    spec = command_spec(name)
    root = Path(workspace).resolve()
    if not root.is_dir():
        raise CommandExecutionError("Workspace does not exist.")
    executable = str(Path(resolve_workspace_executable(spec.executable, root)).resolve())
    if spec.executable == "python":
        import sys
        executable = str(Path(sys.executable).resolve())
    try:
        result = run_absolute_command(
            [executable, *spec.args],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=spec.timeout_seconds,
        )
    except ProcessTimeout:
        return {
            "command": name,
            "argv": [spec.executable, *spec.args],
            "exit_code": None,
            "passed": False,
            "timed_out": True,
            "output": "",
            "output_truncated": False,
            "timeout_seconds": spec.timeout_seconds,
        }
    except Exception as exc:
        raise CommandExecutionError(f"Governed command failed to start: {name}") from exc

    stdout = result.stdout or ""
    stderr = result.stderr or ""
    combined = (stdout + ("\n" if stdout and stderr else "") + stderr).encode("utf-8", errors="replace")
    truncated = len(combined) > spec.max_output_bytes
    if truncated:
        combined = combined[: spec.max_output_bytes]
    output = combined.decode("utf-8", errors="replace")
    return {
        "command": name,
        "argv": [spec.executable, *spec.args],
        "exit_code": result.returncode,
        "passed": result.returncode == 0,
        "timed_out": False,
        "output": output,
        "output_truncated": truncated,
        "timeout_seconds": spec.timeout_seconds,
    }


def supported_commands() -> list[str]:
    return sorted(_COMMANDS)

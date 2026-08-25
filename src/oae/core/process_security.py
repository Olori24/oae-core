"""Validated process-execution boundaries for OAE-controlled local tools.

This module is intentionally the only OAE core location that invokes subprocesses
directly. Callers must use a resolved executable and validate their domain-specific
operands before reaching this boundary.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess  # nosec B404 - centralized, validated process boundary.
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from urllib.parse import urlparse

ProcessExecutionError = subprocess.CalledProcessError
ProcessTimeout = subprocess.TimeoutExpired

_GIT_SUBCOMMANDS = frozenset(
    {
        "add",
        "branch",
        "checkout",
        "clone",
        "commit",
        "diff",
        "fetch",
        "log",
        "pull",
        "push",
        "status",
        "--version",
    }
)
_DISALLOWED_GIT_ARGUMENTS = frozenset(
    {
        "-c",
        "--config-env",
        "--exec",
        "--git-dir",
        "--namespace",
        "--receive-pack",
        "--upload-pack",
        "--work-tree",
    }
)
_GIT_REF = re.compile(r"(?!-)(?!.*\.\.)(?!.*@\{)[A-Za-z0-9][A-Za-z0-9._/-]{0,254}")
_GIT_REMOTE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
_REPOSITORY_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_ALLOWED_TEST_TOOLS = frozenset({"python", "pytest", "ruff", "mypy"})


class ProcessPolicyError(ValueError):
    """Raised when a caller requests a process outside OAE's local policy."""


def resolve_executable(name: str) -> str:
    """Resolve an allowlisted executable to an absolute, executable local path."""
    if not isinstance(name, str) or not name or Path(name).name != name:
        raise ProcessPolicyError("Executable name must be a simple local command name.")
    resolved = shutil.which(name)
    if resolved is None:
        raise ProcessPolicyError(f"Required executable is unavailable: {name}")
    path = Path(resolved).resolve()
    if not path.is_file() or not os.access(path, os.X_OK):
        raise ProcessPolicyError(f"Resolved executable is not runnable: {name}")
    return str(path)


def validate_working_directory(cwd: str | Path | None) -> Path | None:
    """Resolve and require a local working directory before process execution."""
    if cwd is None:
        return None
    path = Path(cwd).resolve()
    if not path.is_dir():
        raise ProcessPolicyError(f"Process working directory does not exist: {path}")
    return path


def validate_git_ref(value: str) -> str:
    """Accept a bounded Git ref name without option, revision-expression, or traversal syntax."""
    if not isinstance(value, str) or not _GIT_REF.fullmatch(value) or value.endswith("/"):
        raise ProcessPolicyError("Git ref contains unsupported syntax.")
    return value


def validate_git_remote(value: str) -> str:
    """Accept a simple named Git remote, never a command-line option."""
    if not isinstance(value, str) or not _GIT_REMOTE.fullmatch(value):
        raise ProcessPolicyError("Git remote contains unsupported syntax.")
    return value


def validate_repository_url(value: str) -> str:
    """Allow credential-free HTTPS clone sources with a bounded final path component."""
    if not isinstance(value, str):
        raise ProcessPolicyError("Repository URL must be text.")
    parsed = urlparse(value)
    try:
        has_port = parsed.port is not None
    except ValueError as exc:
        raise ProcessPolicyError("Repository URL contains an invalid port.") from exc
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or has_port
        or parsed.query
        or parsed.fragment
    ):
        raise ProcessPolicyError("Repository URL must be credential-free HTTPS without a port or query.")
    path_parts = [part for part in parsed.path.split("/") if part]
    if len(path_parts) < 2 or any(part in {".", ".."} for part in path_parts):
        raise ProcessPolicyError("Repository URL must contain a normal repository path.")
    repository_name = path_parts[-1].removesuffix(".git")
    if not _REPOSITORY_NAME.fullmatch(repository_name):
        raise ProcessPolicyError("Repository URL has an unsupported repository name.")
    return value


def repository_name_from_url(value: str) -> str:
    """Derive a safe local directory name only after URL validation."""
    validated = validate_repository_url(value)
    return [part for part in urlparse(validated).path.split("/") if part][-1].removesuffix(".git")


def run_absolute_command(
    command: Sequence[str],
    *,
    cwd: str | Path | None = None,
    check: bool = False,
    capture_output: bool = True,
    text: bool = True,
    timeout: float | None = None,
    env: Mapping[str, str] | None = None,
):
    """Run an absolute local executable after basic argument and cwd validation."""
    tokens = _validate_command(command)
    return subprocess.run(  # nosec B603 - executable and cwd are validated at this boundary.
        tokens,
        cwd=validate_working_directory(cwd),
        check=check,
        capture_output=capture_output,
        text=text,
        timeout=timeout,
        env=env,
    )


def popen_absolute_command(
    command: Sequence[str],
    *,
    cwd: str | Path | None = None,
    stdout=None,
    stderr=None,
    capture_output: bool = False,
    text: bool = True,
):
    """Start an absolute local executable with the same argument and cwd boundary checks."""
    tokens = _validate_command(command)
    if capture_output and (stdout is not None or stderr is not None):
        raise ProcessPolicyError("Specify captured streams or explicit streams, not both.")
    if capture_output:
        stdout = subprocess.PIPE
        stderr = subprocess.PIPE
    return subprocess.Popen(  # nosec B603 - executable and cwd are validated at this boundary.
        tokens,
        cwd=validate_working_directory(cwd),
        stdout=stdout,
        stderr=stderr,
        text=text,
    )


def run_git(
    arguments: Sequence[str],
    *,
    cwd: str | Path | None = None,
    check: bool = False,
    capture_output: bool = True,
    text: bool = True,
    timeout: float | None = None,
):
    """Run a constrained Git invocation through the absolute process boundary."""
    tokens = _validate_git_arguments(arguments)
    return run_absolute_command(
        [resolve_executable("git"), *tokens],
        cwd=cwd,
        check=check,
        capture_output=capture_output,
        text=text,
        timeout=timeout,
    )


def run_allowed_test_command(command: Sequence[str], *, cwd: str | Path | None = None):
    """Run a local test or quality tool from a deliberately short allowlist."""
    tokens = _validate_tokens(command)
    tool = tokens[0]
    if tool not in _ALLOWED_TEST_TOOLS:
        raise ProcessPolicyError("Repository test runner allows only python, pytest, ruff, or mypy.")
    if tool == "python":
        if "-c" in tokens or "-" in tokens:
            raise ProcessPolicyError("Repository test runner does not allow arbitrary Python code execution.")
        executable = str(Path(sys.executable).resolve())
    else:
        executable = resolve_executable(tool)
    return run_absolute_command([executable, *tokens[1:]], cwd=cwd, check=False)


def _validate_command(command: Sequence[str]) -> list[str]:
    tokens = _validate_tokens(command)
    executable = Path(tokens[0])
    if not executable.is_absolute() or not executable.is_file() or not os.access(executable, os.X_OK):
        raise ProcessPolicyError("Process executable must be an absolute runnable local file.")
    return [str(executable.resolve()), *tokens[1:]]


def _validate_tokens(command: Sequence[str]) -> list[str]:
    if isinstance(command, (str, bytes)) or not command:
        raise ProcessPolicyError("Process command must be a non-empty sequence of text arguments.")
    tokens = list(command)
    if not all(isinstance(token, str) and token and "\x00" not in token for token in tokens):
        raise ProcessPolicyError("Process command contains an invalid argument.")
    return tokens


def _validate_git_arguments(arguments: Sequence[str]) -> list[str]:
    tokens = _validate_tokens(arguments)
    if tokens[0] not in _GIT_SUBCOMMANDS:
        raise ProcessPolicyError("Git subcommand is not approved for this execution boundary.")
    if any(token in _DISALLOWED_GIT_ARGUMENTS for token in tokens):
        raise ProcessPolicyError("Git command contains a disallowed global execution option.")
    return tokens

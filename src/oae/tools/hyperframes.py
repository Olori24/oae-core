"""OAE adapter for deterministic HyperFrames video production.

HyperFrames remains the rendering engine; OAE owns orchestration, governance,
job metadata, and verification. This module deliberately shells out to the
official HyperFrames CLI rather than reimplementing its renderer.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess


class HyperFramesError(RuntimeError):
    """Raised when the HyperFrames toolchain cannot complete a request."""


@dataclass(frozen=True)
class RenderRequest:
    project_dir: Path
    output_path: Path | None = None
    timeout_seconds: int = 900
    quality: str = "looks"


@dataclass(frozen=True)
class RenderResult:
    project_dir: Path
    output_path: Path | None
    command: tuple[str, ...]


class HyperFramesRunner:
    """Small, testable process boundary around the HyperFrames CLI."""

    executable = "npx"

    def available(self) -> bool:
        return shutil.which(self.executable) is not None

    def _run(self, command: tuple[str, ...], project_dir: Path, timeout: int) -> None:
        try:
            subprocess.run(
                command,
                cwd=project_dir,
                check=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or exc.stdout or "HyperFrames command failed").strip()
            raise HyperFramesError(detail) from exc
        except subprocess.TimeoutExpired as exc:
            raise HyperFramesError(f"HyperFrames command timed out after {timeout}s") from exc

    def _validate_project(self, project_dir: Path) -> None:
        if not project_dir.is_dir():
            raise HyperFramesError(f"Project directory does not exist: {project_dir}")
        if not (project_dir / "index.html").is_file():
            raise HyperFramesError(
                f"HyperFrames project must contain index.html: {project_dir}"
            )
        if not self.available():
            raise HyperFramesError("Node/npx is not installed or not on PATH")

    def lint(self, project_dir: Path, timeout_seconds: int = 120) -> None:
        """Run the fast structural HyperFrames gate."""
        project_dir = project_dir.resolve()
        self._validate_project(project_dir)
        self._run(
            (self.executable, "hyperframes", "lint", "--json"),
            project_dir,
            timeout_seconds,
        )

    def check(self, project_dir: Path, timeout_seconds: int = 300) -> None:
        """Run HyperFrames' browser/runtime/layout/motion/contrast gate."""
        project_dir = project_dir.resolve()
        self._validate_project(project_dir)
        self._run(
            (self.executable, "hyperframes", "check", "--json"),
            project_dir,
            timeout_seconds,
        )

    def render(self, request: RenderRequest) -> RenderResult:
        project_dir = request.project_dir.resolve()
        self._validate_project(project_dir)

        output = (
            request.output_path.resolve()
            if request.output_path
            else project_dir / "renders" / "oae-output.mp4"
        )
        output.parent.mkdir(parents=True, exist_ok=True)

        command = (
            self.executable,
            "hyperframes",
            "render",
            "--quality",
            request.quality,
            "--output",
            str(output),
        )
        self._run(command, project_dir, request.timeout_seconds)

        if not output.is_file() or output.stat().st_size == 0:
            raise HyperFramesError(f"Expected non-empty output was not produced: {output}")

        return RenderResult(project_dir=project_dir, output_path=output, command=command)

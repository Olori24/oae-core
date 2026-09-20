"""OAE adapter for deterministic HyperFrames video rendering.

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

    def render(self, request: RenderRequest) -> RenderResult:
        project_dir = request.project_dir.resolve()
        if not project_dir.is_dir():
            raise HyperFramesError(f"Project directory does not exist: {project_dir}")
        if not (project_dir / "index.html").is_file():
            raise HyperFramesError(
                f"HyperFrames project must contain index.html: {project_dir}"
            )
        if not self.available():
            raise HyperFramesError("Node/npx is not installed or not on PATH")

        command = (self.executable, "hyperframes", "render")
        try:
            completed = subprocess.run(
                command,
                cwd=project_dir,
                check=True,
                capture_output=True,
                text=True,
                timeout=request.timeout_seconds,
            )
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or exc.stdout or "render failed").strip()
            raise HyperFramesError(detail) from exc
        except subprocess.TimeoutExpired as exc:
            raise HyperFramesError(
                f"render timed out after {request.timeout_seconds}s"
            ) from exc

        output = request.output_path.resolve() if request.output_path else None
        if output is not None and not output.is_file():
            raise HyperFramesError(f"Expected output was not produced: {output}")

        # stdout is intentionally not returned: callers should record only the
        # governed job metadata they need, avoiding accidental log leakage.
        _ = completed.stdout
        return RenderResult(project_dir=project_dir, output_path=output, command=command)

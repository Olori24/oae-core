import json
import os
import shutil
import subprocess
from pathlib import Path


class FrontendBuildVerifier:
    """Verify and, when requested, build a generated Next.js frontend.

    This verifier only operates on an OAE-generated application workspace. It
    never installs packages with lifecycle scripts enabled before the build
    step, and it reports every command result instead of treating invocation
    as proof of success.
    """

    def verify(self, root, execute_build=True, timeout=180):
        root = Path(root)
        frontend = root / "web"
        package = frontend / "package.json"

        if not package.is_file():
            return {
                "name": "frontend build",
                "passed": False,
                "status": "blocked",
                "detail": "Missing web/package.json",
                "returncode": None,
            }

        try:
            manifest = json.loads(package.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return self._failure("Invalid web/package.json", exc)

        if manifest.get("scripts", {}).get("build") is None:
            return {
                "name": "frontend build",
                "passed": False,
                "status": "blocked",
                "detail": "package.json has no build script",
                "returncode": None,
            }

        if not execute_build:
            return {
                "name": "frontend build",
                "passed": True,
                "status": "ready",
                "detail": "Frontend build contract is present",
                "returncode": None,
            }

        npm = shutil.which("npm")
        if npm is None:
            return {
                "name": "frontend build",
                "passed": False,
                "status": "blocked",
                "detail": "npm is not installed in the verification environment",
                "returncode": None,
            }

        install = self._run(
            [
                npm,
                "install",
                "--include=dev",
                "--ignore-scripts",
                "--no-audit",
                "--no-fund",
            ],
            frontend,
            timeout,
        )
        if install["returncode"] != 0:
            return {
                "name": "frontend dependency install",
                "passed": False,
                "status": "failed",
                "detail": install["stderr"] or install["stdout"],
                "returncode": install["returncode"],
            }

        build = self._run([npm, "run", "build"], frontend, timeout)
        return {
            "name": "frontend build",
            "passed": build["returncode"] == 0,
            "status": "passed" if build["returncode"] == 0 else "failed",
            "detail": build["stdout"] if build["returncode"] == 0 else build["stderr"],
            "returncode": build["returncode"],
        }

    @staticmethod
    def _run(command, cwd, timeout):
        try:
            environment = os.environ.copy()
            environment["NODE_ENV"] = "production"
            environment.setdefault("NEXT_TELEMETRY_DISABLED", "1")
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                env=environment,
            )
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except subprocess.TimeoutExpired as exc:
            return {
                "returncode": 124,
                "stdout": exc.stdout or "",
                "stderr": f"Frontend verification timed out after {timeout}s",
            }
        except OSError as exc:
            return {
                "returncode": 127,
                "stdout": "",
                "stderr": str(exc),
            }

    @staticmethod
    def _failure(detail, exc):
        return {
            "name": "frontend build",
            "passed": False,
            "status": "blocked",
            "detail": f"{detail}: {exc}",
            "returncode": None,
        }

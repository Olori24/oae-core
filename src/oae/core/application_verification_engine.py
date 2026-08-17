from pathlib import Path
import subprocess
import sys

from oae.core.application_readiness_engine import ApplicationReadinessEngine
from oae.core.project_specification import ProjectSpecification


class ApplicationVerificationEngine:
    """Turn generated-application readiness into executable verification."""

    def __init__(self, readiness=None):
        self.readiness = readiness or ApplicationReadinessEngine()

    def verify(self, root, specification: ProjectSpecification):
        root = Path(root)
        readiness = self.readiness.assess(root, specification)
        checks = list(readiness["checks"])

        if readiness["status"] != "ready":
            return {
                "status": "blocked",
                "readiness": readiness,
                "checks": checks,
                "execution": None,
            }

        execution = self._run_python_contract(root)
        checks.append(execution)

        status = "verified" if execution["passed"] else "failed"
        return {
            "status": status,
            "readiness": readiness,
            "checks": checks,
            "execution": execution,
        }

    @staticmethod
    def _run_python_contract(root):
        main = root / "src" / "main.py"
        completed = subprocess.run(
            [sys.executable, str(main)],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        return {
            "name": "backend executable contract",
            "passed": completed.returncode == 0,
            "detail": completed.stdout.strip()
            if completed.returncode == 0
            else completed.stderr.strip(),
            "returncode": completed.returncode,
        }

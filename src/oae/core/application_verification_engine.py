import sys
from pathlib import Path

from oae.core.application_integration_verifier import ApplicationIntegrationVerifier
from oae.core.application_readiness_engine import ApplicationReadinessEngine
from oae.core.frontend_build_verifier import FrontendBuildVerifier
from oae.core.process_security import run_absolute_command
from oae.core.project_specification import ProjectSpecification


class ApplicationVerificationEngine:
    """Turn generated-application readiness into executable verification."""

    def __init__(self, readiness=None, frontend=None, integration=None):
        self.readiness = readiness or ApplicationReadinessEngine()
        self.frontend = frontend or FrontendBuildVerifier()
        self.integration = integration or ApplicationIntegrationVerifier()

    def verify(
        self,
        root,
        specification: ProjectSpecification,
        execute_frontend_build=False,
        execute_integration=False,
    ):
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

        backend = self._run_python_contract(root)
        checks.append(backend)

        frontend = self.frontend.verify(
            root,
            execute_build=execute_frontend_build,
        )
        checks.append(frontend)

        integration = self.integration.verify(root, specification) if execute_integration else {
            "name": "backend/frontend integration",
            "passed": True,
            "status": "ready",
            "detail": "Live integration verification deferred",
        }
        checks.append(integration)

        passed = backend["passed"] and frontend["passed"] and integration["passed"]
        status = "verified" if passed else "failed"
        return {
            "status": status,
            "readiness": readiness,
            "checks": checks,
            "execution": {
                "backend": backend,
                "frontend": frontend,
                "integration": integration,
            },
        }

    @staticmethod
    def _run_python_contract(root):
        main = root / "src" / "main.py"
        completed = run_absolute_command(
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

import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from oae.core.project_specification import ProjectSpecification


class ApplicationIntegrationVerifier:
    """Verify that a generated FastAPI backend can serve its health contract."""

    def verify(self, root, specification: ProjectSpecification, timeout=30):
        root = Path(root)
        if specification.framework != "FastAPI":
            return {
                "name": "backend/frontend integration",
                "passed": False,
                "status": "blocked",
                "detail": f"Integration verifier requires FastAPI, got {specification.framework}",
            }

        main = root / "src" / "main.py"
        if not main.is_file():
            return self._blocked("Missing src/main.py")

        if not (root / "src" / "api" / "health.py").is_file():
            return self._blocked("Missing generated health contract")

        command = [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8765"]
        process = subprocess.Popen(
            command,
            cwd=root / "src",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            deadline = time.monotonic() + timeout
            response = None
            last_error = None
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    break
                try:
                    with urllib.request.urlopen("http://127.0.0.1:8765/health", timeout=2) as result:
                        response = result.read().decode("utf-8")
                    break
                except (urllib.error.URLError, TimeoutError) as exc:
                    last_error = str(exc)
                    time.sleep(0.25)

            if response is None:
                stderr = process.stderr.read() if process.stderr else ""
                return {
                    "name": "backend/frontend integration",
                    "passed": False,
                    "status": "failed",
                    "detail": stderr.strip() or last_error or "Health endpoint did not become available",
                }

            passed = '"status":"healthy"' in response.replace(" ", "")
            return {
                "name": "backend/frontend integration",
                "passed": passed,
                "status": "passed" if passed else "failed",
                "detail": response,
            }
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

    @staticmethod
    def _blocked(detail):
        return {
            "name": "backend/frontend integration",
            "passed": False,
            "status": "blocked",
            "detail": detail,
        }

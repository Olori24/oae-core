import http.client
import subprocess
import sys
import time
from pathlib import Path

from oae.core.project_specification import ProjectSpecification


class ApplicationIntegrationVerifier:
    """Verify that a generated FastAPI backend can serve its health contract."""

    _LOOPBACK_HOST = "127.0.0.1"
    _HEALTH_PORT = 8765
    _MAX_HEALTH_RESPONSE_BYTES = 8_192

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

        command = [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            self._LOOPBACK_HOST,
            "--port",
            str(self._HEALTH_PORT),
        ]
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
                    response = self._read_loopback_health()
                    break
                except (http.client.HTTPException, OSError, TimeoutError, ValueError) as exc:
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

    @classmethod
    def _read_loopback_health(cls) -> str:
        """Read only the fixed local health endpoint with a bounded response body."""
        connection = http.client.HTTPConnection(cls._LOOPBACK_HOST, cls._HEALTH_PORT, timeout=2)
        try:
            connection.request("GET", "/health", headers={"Accept": "application/json"})
            result = connection.getresponse()
            if result.status != 200:
                raise ValueError(f"Loopback health endpoint returned HTTP {result.status}")
            content_type = result.getheader("Content-Type", "").lower()
            if "application/json" not in content_type:
                raise ValueError("Loopback health endpoint did not return JSON")
            body = result.read(cls._MAX_HEALTH_RESPONSE_BYTES + 1)
            if len(body) > cls._MAX_HEALTH_RESPONSE_BYTES:
                raise ValueError("Loopback health endpoint exceeded the response size limit")
            return body.decode("utf-8")
        finally:
            connection.close()

    @staticmethod
    def _blocked(detail):
        return {
            "name": "backend/frontend integration",
            "passed": False,
            "status": "blocked",
            "detail": detail,
        }

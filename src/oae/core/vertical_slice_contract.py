from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VerticalSliceContract:
    """Minimum contract for a generated, testable full-stack application."""

    backend_health_path: str = "/health"
    frontend_api_module: str = "web/lib/api.ts"
    backend_entrypoint: str = "src/main.py"

    def validate(self, root):
        root = Path(root)
        checks = {
            "backend_entrypoint": (root / self.backend_entrypoint).is_file(),
            "frontend_api_module": (root / self.frontend_api_module).is_file(),
            "health_path": self.backend_health_path == "/health",
        }
        return {
            "passed": all(checks.values()),
            "checks": checks,
        }

from dataclasses import dataclass
from pathlib import Path

from oae.core.project_specification import ProjectSpecification


@dataclass(frozen=True)
class ReadinessCheck:
    name: str
    passed: bool
    detail: str


class ApplicationReadinessEngine:
    """Evaluate whether a generated application has the required structural contracts.

    This engine is intentionally non-destructive: it inspects a generated project and
    reports missing contracts. Build/test execution remains the responsibility of the
    governed execution and verification layers.
    """

    REQUIRED_BACKEND = (
        "pyproject.toml",
        "src/main.py",
    )
    REQUIRED_FRONTEND = (
        "web/package.json",
        "web/tsconfig.json",
        "web/app/layout.tsx",
        "web/app/page.tsx",
        "web/lib/api.ts",
    )
    REQUIRED_OPERATIONS = (
        "create_file",
        "modify_file",
        "run_tests",
    )

    def assess(self, root, specification: ProjectSpecification):
        root = Path(root)
        checks = []

        checks.append(self._file_check(root, "project", "pyproject.toml"))
        checks.append(self._file_check(root, "backend entrypoint", "src/main.py"))

        if specification.frontend_framework == "Next.js":
            checks.extend(
                self._file_check(root, "frontend", path)
                for path in self.REQUIRED_FRONTEND
            )
        else:
            checks.append(
                ReadinessCheck(
                    "frontend framework",
                    False,
                    f"Unsupported frontend framework: {specification.frontend_framework}",
                )
            )

        if specification.docker:
            checks.append(self._file_check(root, "containerization", "Dockerfile"))
        if specification.ci:
            checks.append(
                self._directory_file_check(root, "CI", ".github/workflows")
            )

        checks.append(
            ReadinessCheck(
                "operation vocabulary",
                True,
                ", ".join(self.REQUIRED_OPERATIONS),
            )
        )

        passed = sum(check.passed for check in checks)
        total = len(checks)
        return {
            "status": "ready" if passed == total else "blocked",
            "passed": passed,
            "total": total,
            "score": round((passed / total) * 100) if total else 0,
            "checks": [check.__dict__ for check in checks],
        }

    @staticmethod
    def _file_check(root, name, relative):
        path = root / relative
        return ReadinessCheck(
            name,
            path.is_file(),
            str(relative) if path.is_file() else f"Missing {relative}",
        )

    @staticmethod
    def _directory_file_check(root, name, relative):
        path = root / relative
        exists = path.is_dir() and any(path.iterdir())
        return ReadinessCheck(
            name,
            exists,
            str(relative) if exists else f"Missing populated {relative}",
        )

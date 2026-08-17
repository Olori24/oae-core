from pathlib import Path

from oae.core.application_readiness_engine import ApplicationReadinessEngine
from oae.core.project_specification import ProjectSpecification


def specification():
    return ProjectSpecification(
        name="Demo",
        description="A generated application",
        language="Python",
        framework="FastAPI",
        database="PostgreSQL",
        testing_framework="pytest",
    )


def create_contract(root: Path):
    for relative in (
        "pyproject.toml",
        "src/main.py",
        "web/package.json",
        "web/tsconfig.json",
        "web/app/layout.tsx",
        "web/app/page.tsx",
        "web/lib/api.ts",
        "Dockerfile",
        ".github/workflows/test.yml",
    ):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# contract\n", encoding="utf-8")


def test_ready_generated_application(tmp_path):
    create_contract(tmp_path)

    result = ApplicationReadinessEngine().assess(tmp_path, specification())

    assert result["status"] == "ready"
    assert result["score"] == 100
    assert result["passed"] == result["total"]


def test_missing_contract_blocks_readiness(tmp_path):
    create_contract(tmp_path)
    (tmp_path / "web/app/page.tsx").unlink()

    result = ApplicationReadinessEngine().assess(tmp_path, specification())

    assert result["status"] == "blocked"
    assert result["score"] < 100
    assert any(
        check["name"] == "frontend" and not check["passed"]
        for check in result["checks"]
    )

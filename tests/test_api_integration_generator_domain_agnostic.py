
from oae.core.api_integration_generator import ApiIntegrationGenerator
from oae.core.project_specification import ProjectSpecification


def test_api_integration_uses_project_name_and_generated_routers(tmp_path):
    api = tmp_path / "src/api"
    api.mkdir(parents=True)
    (api / "__init__.py").write_text("", encoding="utf-8")
    (api / "health.py").write_text("router = object()\n", encoding="utf-8")
    (api / "jobs.py").write_text("router = object()\n", encoding="utf-8")
    main = tmp_path / "src/main.py"
    main.write_text("# scaffold\n", encoding="utf-8")

    spec = ProjectSpecification(
        name="TeamPulse",
        description="Engineering workspace",
        language="Python",
        framework="FastAPI",
        database="SQLite",
        testing_framework="pytest",
    )

    ApiIntegrationGenerator().generate(tmp_path, spec)
    text = main.read_text(encoding="utf-8")

    assert 'title="TeamPulse"' in text
    assert "from src.api.health import router as health_router" in text
    assert "from src.api.jobs import router as jobs_router" in text
    assert "Opportunity Radar Africa" not in text

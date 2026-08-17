from oae.core.api_integration_generator import ApiIntegrationGenerator
from oae.core.project_specification import ProjectSpecification


def test_generate_is_domain_agnostic(tmp_path):
    src = tmp_path / "src"
    api = src / "api"
    api.mkdir(parents=True)
    (src / "main.py").write_text("# scaffold\n", encoding="utf-8")
    (api / "health.py").write_text("router = object()\n", encoding="utf-8")
    (api / "jobs.py").write_text("router = object()\n", encoding="utf-8")

    specification = ProjectSpecification(
        name="TeamPulse",
        description="Developer workspace",
        language="Python",
        framework="FastAPI",
        database="SQLite",
        testing_framework="pytest",
    )

    ApiIntegrationGenerator().generate(tmp_path, specification)
    generated = (src / "main.py").read_text(encoding="utf-8")

    assert 'title="TeamPulse"' in generated
    assert "from src.api.health import router as health_router" in generated
    assert "from src.api.jobs import router as jobs_router" in generated
    assert "Opportunity Radar Africa" not in generated

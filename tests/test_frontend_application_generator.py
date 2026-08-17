from oae.core.frontend_application_generator import FrontendApplicationGenerator
from oae.core.project_specification import ProjectSpecification


def test_frontend_generator_creates_governed_next_application(tmp_path):
    spec = ProjectSpecification(name="Demo", description="Demo", language="Python", framework="FastAPI", database="SQLite", testing_framework="pytest")
    root = FrontendApplicationGenerator().generate(tmp_path, spec)
    assert root == tmp_path / "web"
    assert (root / "package.json").exists()
    assert (root / "app" / "layout.tsx").exists()
    assert (root / "app" / "page.tsx").exists()
    assert (root / "app" / "globals.css").exists()
    assert (root / "lib" / "api.ts").exists()


def test_frontend_generator_connects_to_backend_health_boundary(tmp_path):
    spec = ProjectSpecification(name="Demo", description="Demo", language="Python", framework="FastAPI", database="SQLite", testing_framework="pytest")
    root = FrontendApplicationGenerator().generate(tmp_path, spec)
    api_client = (root / "lib" / "api.ts").read_text()
    page = (root / "app" / "page.tsx").read_text()
    assert "NEXT_PUBLIC_API_URL" in api_client
    assert "/health" in api_client
    assert "getHealth" in page
    assert "OAE GENERATED APPLICATION" in page

from oae.core.project_bootstrap_orchestrator import ProjectBootstrapOrchestrator
from oae.core.project_specification import ProjectSpecification


def test_bootstrap_includes_frontend_application(tmp_path):
    spec = ProjectSpecification(name="Demo", description="Demo", language="Python", framework="FastAPI", database="SQLite", testing_framework="pytest")
    root = ProjectBootstrapOrchestrator().bootstrap(tmp_path / "demo", spec)
    assert (root / "web" / "package.json").exists()
    assert (root / "web" / "app" / "page.tsx").exists()

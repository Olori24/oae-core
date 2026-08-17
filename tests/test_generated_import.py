import importlib.util

from oae.core.executable_application_generator import ExecutableApplicationGenerator
from oae.core.project_specification import ProjectSpecification


def test_generated_fastapi_entrypoint_is_importable(tmp_path):
    specification = ProjectSpecification(
        name="TeamPulse",
        description="A developer workspace.",
        language="Python",
        framework="FastAPI",
        database="SQLite",
        testing_framework="pytest",
    )
    ExecutableApplicationGenerator().generate(tmp_path, specification)
    module_path = tmp_path / "src" / "main.py"
    spec = importlib.util.spec_from_file_location("generated_main", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.app.title == "TeamPulse"
    assert module.health_endpoint()["status"] == "healthy"

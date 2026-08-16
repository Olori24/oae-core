from pathlib import Path

from oae.core.project_specification import ProjectSpecification


class ApplicationScaffoldGenerator:
    """
    Generates the first runnable application scaffold.
    """

    def generate(self, root, specification: ProjectSpecification):
        root = Path(root)

        src = root / "src"

        directories = [
            src,
            src / "api",
            src / "config",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

        (src / "__init__.py").write_text("")
        (src / "api" / "__init__.py").write_text("")
        (src / "config" / "__init__.py").write_text("")

        (src / "main.py").write_text(
f'''def main():
    print("{specification.name}")
    print("Status: READY")

if __name__ == "__main__":
    main()
'''
        )

        (src / "api" / "health.py").write_text(
f'''def health():
    return {{
        "status": "healthy",
        "service": "{specification.name}",
    }}
'''
        )

        (src / "config" / "settings.py").write_text(
'''APP_ENV = "development"
'''
        )

        tests = root / "tests"
        tests.mkdir(parents=True, exist_ok=True)

        (tests / "test_health.py").write_text(
f'''from src.api.health import health


def test_health():
    result = health()

    assert result["status"] == "healthy"
    assert result["service"] == "{specification.name}"
'''
        )

        return True

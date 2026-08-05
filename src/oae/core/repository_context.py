from dataclasses import dataclass
from pathlib import Path


@dataclass
class RepositoryContext:
    language: str
    framework: str
    package_manager: str
    has_tests: bool
    has_readme: bool
    has_git: bool


class RepositoryContextEngine:
    """
    Discovers repository technology.
    """

    def __init__(self, repository: str | Path = "."):
        self.repository = Path(repository)

    def analyze(self) -> RepositoryContext:

        language = "Unknown"
        framework = "Unknown"
        package_manager = "Unknown"

        if list(self.repository.rglob("*.py")):
            language = "Python"

        if (self.repository / "requirements.txt").exists():
            package_manager = "pip"

        if (self.repository / "pyproject.toml").exists():
            package_manager = "poetry"

        if (self.repository / "package.json").exists():
            language = "JavaScript"
            package_manager = "npm"

        if (self.repository / "manage.py").exists():
            framework = "Django"

        if (self.repository / "requirements.txt").exists():
            text = (self.repository / "requirements.txt").read_text().lower()

            if "fastapi" in text:
                framework = "FastAPI"

            elif "flask" in text:
                framework = "Flask"

        has_tests = (self.repository / "tests").exists()

        has_readme = (
            (self.repository / "README.md").exists()
            or (self.repository / "README.rst").exists()
        )

        has_git = (self.repository / ".git").exists()

        return RepositoryContext(
            language=language,
            framework=framework,
            package_manager=package_manager,
            has_tests=has_tests,
            has_readme=has_readme,
            has_git=has_git,
        )
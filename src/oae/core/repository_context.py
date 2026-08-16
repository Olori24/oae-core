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
    """Discover the primary technology used by a repository."""

    def __init__(self, repository: str | Path = "."):
        self.repository = Path(repository)

    def analyze(self) -> RepositoryContext:
        language = "Unknown"
        framework = "Unknown"
        package_manager = "Unknown"

        has_python = bool(list(self.repository.rglob("*.py")))
        has_pyproject = (self.repository / "pyproject.toml").exists()
        has_requirements = (self.repository / "requirements.txt").exists()
        has_package_json = (self.repository / "package.json").exists()

        if has_python or has_pyproject or has_requirements:
            language = "Python"
            if has_pyproject:
                package_manager = "poetry"
            elif has_requirements:
                package_manager = "pip"
        elif has_package_json:
            language = "JavaScript"
            package_manager = "npm"

        if (self.repository / "manage.py").exists():
            framework = "Django"

        if has_requirements:
            text = (self.repository / "requirements.txt").read_text().lower()
            if "fastapi" in text:
                framework = "FastAPI"
            elif "flask" in text:
                framework = "Flask"
        elif has_pyproject:
            text = (self.repository / "pyproject.toml").read_text().lower()
            if "fastapi" in text:
                framework = "FastAPI"
            elif "flask" in text:
                framework = "Flask"

        return RepositoryContext(
            language=language,
            framework=framework,
            package_manager=package_manager,
            has_tests=(self.repository / "tests").exists(),
            has_readme=(
                (self.repository / "README.md").exists()
                or (self.repository / "README.rst").exists()
            ),
            has_git=(self.repository / ".git").exists(),
        )

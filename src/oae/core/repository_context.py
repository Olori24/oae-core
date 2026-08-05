from dataclasses import dataclass
from pathlib import Path


@dataclass
class RepositoryContext:
    language: str
    has_tests: bool
    has_readme: bool
    has_git: bool


class RepositoryContextEngine:
    """
    Discovers basic information about a repository.
    """

    def __init__(self, repository: str | Path = "."):
        self.repository = Path(repository)

    def analyze(self) -> RepositoryContext:
        language = "Unknown"

        if list(self.repository.rglob("*.py")):
            language = "Python"

        has_tests = (self.repository / "tests").exists()

        has_readme = (
            (self.repository / "README.md").exists()
            or (self.repository / "README.rst").exists()
        )

        has_git = (self.repository / ".git").exists()

        return RepositoryContext(
            language=language,
            has_tests=has_tests,
            has_readme=has_readme,
            has_git=has_git,
        )
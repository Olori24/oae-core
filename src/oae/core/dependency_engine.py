from dataclasses import dataclass
from pathlib import Path


@dataclass
class DependencyReport:
    dependencies: list[str]


class DependencyEngine:
    """
    Reads repository dependencies.
    """

    def __init__(self, repository: str | Path = "."):
        self.repository = Path(repository)

    def analyze(self) -> DependencyReport:
        dependencies = []

        requirements = self.repository / "requirements.txt"

        if requirements.exists():
            for line in requirements.read_text().splitlines():
                line = line.strip()

                if not line:
                    continue

                if line.startswith("#"):
                    continue

                dependencies.append(line)

        return DependencyReport(
            dependencies=dependencies,
        )
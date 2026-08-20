from dataclasses import dataclass
from pathlib import Path

from oae.core.dependency_classifier import (
    ClassifiedDependency,
    DependencyClassifier,
)


@dataclass
class DependencyReport:
    dependencies: list[ClassifiedDependency]


class DependencyEngine:
    """
    Reads and classifies repository dependencies.
    """

    def __init__(self, repository: str | Path = "."):
        self.repository = Path(repository)
        self.classifier = DependencyClassifier()

    def analyze(self) -> DependencyReport:
        dependencies = []

        requirements = self.repository / "requirements.txt"

        if requirements.exists():
            for line in requirements.read_text().splitlines():
                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                dependencies.append(
                    self.classifier.classify(line)
                )

        return DependencyReport(
            dependencies=dependencies,
        )
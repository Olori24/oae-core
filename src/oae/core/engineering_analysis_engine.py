from oae.core.dead_code_detector import DeadCodeDetector
from oae.core.duplicate_code_detector import DuplicateCodeDetector
from oae.core.circular_dependency_detector import CircularDependencyDetector


class EngineeringAnalysisEngine:
    """
    Runs all repository engineering analyses.
    """

    def __init__(self):
        self.dead_code = DeadCodeDetector()
        self.duplicates = DuplicateCodeDetector()
        self.circular = CircularDependencyDetector()

    def analyze(self, repository_graph):
        return {
            "dead_code": self.dead_code.analyze(repository_graph),
            "duplicates": self.duplicates.analyze(repository_graph),
            "circular_dependencies": self.circular.analyze(repository_graph),
        }

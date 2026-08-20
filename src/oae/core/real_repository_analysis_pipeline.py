from oae.core.repository_knowledge_graph import RepositoryKnowledgeGraph
from oae.core.repository_scanner import RepositoryScanner


class RealRepositoryAnalysisPipeline:
    """
    End-to-end analysis of a real repository.
    """

    def __init__(self):
        self.scanner = RepositoryScanner()
        self.graph = RepositoryKnowledgeGraph()

    def analyze(self, repository_path):
        files = self.scanner.scan(repository_path)

        knowledge = self.graph.build(files)

        return {
            "files": len(files),
            "knowledge": knowledge,
        }
from oae.core.repository_scanner import RepositoryScanner
from oae.core.repository_knowledge_graph import RepositoryKnowledgeGraph


class RepositoryIntelligenceBuilder:
    """
    Builds repository intelligence from a real repository.
    """

    def __init__(self):
        self.scanner = RepositoryScanner()
        self.graph = RepositoryKnowledgeGraph()

    def build(self, repository_path):
        files = self.scanner.scan(repository_path)

        graph = self.graph.build(files)

        return {
            "files": files,
            "knowledge": graph,
            "graph": graph,
        }

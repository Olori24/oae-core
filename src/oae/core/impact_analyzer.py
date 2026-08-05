from dataclasses import dataclass

from oae.core.knowledge_graph import KnowledgeGraph


@dataclass
class ImpactReport:
    target: str
    affected: list[str]


class ImpactAnalyzer:
    """
    Uses the knowledge graph to estimate change impact.
    """

    def __init__(self, graph: KnowledgeGraph):
        self.graph = graph

    def analyze(self, target: str) -> ImpactReport:
        return ImpactReport(
            target=target,
            affected=self.graph.neighbors(target),
        )
class ImpactAnalyzer:
    """
    Determines the impact of changing nodes in a knowledge graph.
    """

    def __init__(self, graph):
        self.graph = graph

    def impacted(self, target):
        impacted = []

        for source, targets in self.graph.edges.items():
            if target in targets:
                impacted.append(source)

        return impacted

    def risk(self, target):
        count = len(self.impacted(target))

        if count >= 5:
            return "HIGH"

        if count >= 2:
            return "MEDIUM"

        return "LOW"

    def report(self, target):
        impacted = self.impacted(target)

        return {
            "target": target,
            "impacted": impacted,
            "count": len(impacted),
            "risk": self.risk(target),
        }
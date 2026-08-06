class ImpactAnalyzer:
    """
    Determines the impact of modifying a symbol.
    """

    def impacted_functions(self, call_graph, target):
        impacted = []

        for caller, callees in call_graph.items():
            if target in callees:
                impacted.append(caller)

        return impacted

    def risk(self, call_graph, target):
        impacted = self.impacted_functions(call_graph, target)

        count = len(impacted)

        if count >= 5:
            return "HIGH"

        if count >= 2:
            return "MEDIUM"

        return "LOW"

    def report(self, call_graph, target):
        impacted = self.impacted_functions(call_graph, target)

        return {
            "target": target,
            "impacted": impacted,
            "risk": self.risk(call_graph, target),
            "count": len(impacted),
        }
class CircularDependencyDetector:
    """
    Detects circular imports in a repository graph.
    """

    def analyze(self, repository_graph):
        findings = []

        visited = set()

        def dfs(node, stack):
            if node in stack:
                cycle = stack[stack.index(node):] + [node]

                findings.append({
                    "cycle": cycle,
                    "severity": "HIGH",
                })
                return

            if node in visited:
                return

            visited.add(node)

            imports = repository_graph.get(node, {}).get("imports", [])

            for dependency in imports:
                if dependency in repository_graph:
                    dfs(dependency, stack + [node])

        for module in repository_graph:
            dfs(module, [])

        return findings

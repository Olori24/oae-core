class DependencyExplorer:
    """
    Explores dependencies inside the repository knowledge graph.
    """

    def imports_of(self, graph, filename):
        if filename not in graph:
            return []

        return graph[filename]["imports"]

    def files_importing(self, graph, module):
        users = []

        for filename, data in graph.items():
            if module in data["imports"]:
                users.append(filename)

        return users

    def functions(self, graph):
        result = []

        for data in graph.values():
            result.extend(data["functions"])

        return result

    def classes(self, graph):
        result = []

        for data in graph.values():
            result.extend(data["classes"])

        return result
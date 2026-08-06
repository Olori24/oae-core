class SymbolResolver:
    """
    Resolves where functions and classes are defined.
    """

    def resolve_function(self, graph, function_name):
        for filename, data in graph.items():
            if function_name in data.get("functions", []):
                return filename

        return None

    def resolve_class(self, graph, class_name):
        for filename, data in graph.items():
            if class_name in data.get("classes", []):
                return filename

        return None

    def symbols(self, graph):
        result = {}

        for filename, data in graph.items():
            for function in data.get("functions", []):
                result[function] = filename

            for cls in data.get("classes", []):
                result[cls] = filename

        return result
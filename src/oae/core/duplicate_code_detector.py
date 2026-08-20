class DuplicateCodeDetector:
    """
    Detects duplicated function names across a repository.
    """

    def analyze(self, repository_graph):
        seen: dict[str, str] = {}
        duplicates: list[dict[str, object]] = []

        for filename, data in repository_graph.items():
            for function in data.get("functions", []):

                if function in seen:
                    duplicates.append({
                        "function": function,
                        "files": [
                            seen[function],
                            filename,
                        ],
                        "severity": "MEDIUM",
                    })
                else:
                    seen[function] = filename

        return duplicates

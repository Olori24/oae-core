class DeadCodeDetector:
    """
    Detects obvious dead code from repository knowledge.
    """

    def analyze(self, repository_graph):
        findings = []

        for filename, data in repository_graph.items():

            functions = data.get("functions", [])
            classes = data.get("classes", [])
            imports = data.get("imports", [])

            if (
                not functions
                and not classes
                and not imports
            ):
                findings.append({
                    "type": "empty_module",
                    "file": filename,
                    "severity": "LOW",
                })

            elif (
                not functions
                and not classes
                and imports
            ):
                findings.append({
                    "type": "imports_only",
                    "file": filename,
                    "severity": "MEDIUM",
                })

        return findings

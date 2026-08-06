class RepositoryIntelligenceEngine:
    """
    Classifies repository findings into engineering intelligence.
    """

    def classify(self, findings):
        intelligence = []

        for finding in findings:
            intelligence.append(
                {
                    "finding": finding,
                    "category": self._category(finding),
                    "priority": self._priority(finding),
                }
            )

        return intelligence

    def _category(self, finding):
        text = finding.lower()

        if "security" in text:
            return "security"

        if "test" in text:
            return "quality"

        if "performance" in text:
            return "performance"

        if "dependency" in text:
            return "architecture"

        return "general"

    def _priority(self, finding):
        text = finding.lower()

        if "security" in text:
            return 10

        if "performance" in text:
            return 8

        if "test" in text:
            return 6

        return 5
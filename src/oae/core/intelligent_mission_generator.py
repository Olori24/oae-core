class IntelligentMissionGenerator:
    """
    Generates intelligent engineering missions from repository intelligence.
    """

    def generate(self, intelligence):
        missions = []

        for item in intelligence:
            missions.append(
                {
                    "title": self._title(item),
                    "category": item["category"],
                    "priority": item["priority"],
                    "recommended_agent": self._agent(item["category"]),
                }
            )

        return missions

    def _title(self, item):
        return f"Resolve {item['finding']}"

    def _agent(self, category):
        mapping = {
            "security": "Security Engineer",
            "quality": "QA Engineer",
            "performance": "Backend Engineer",
            "architecture": "Architect Agent",
            "general": "Backend Engineer",
        }

        return mapping.get(category, "Backend Engineer")
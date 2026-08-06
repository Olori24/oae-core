class EngineeringRecommendationEngine:
    """
    Converts engineering analysis into prioritized engineering missions.
    """

    def recommend(self, analysis):
        missions = []

        for item in analysis.get("circular_dependencies", []):
            missions.append({
                "priority": "HIGH",
                "type": "break_circular_dependency",
                "details": item,
            })

        for item in analysis.get("dead_code", []):
            missions.append({
                "priority": "MEDIUM",
                "type": "remove_dead_code",
                "details": item,
            })

        for item in analysis.get("duplicates", []):
            missions.append({
                "priority": "LOW",
                "type": "merge_duplicate_code",
                "details": item,
            })

        priority = {
            "HIGH": 0,
            "MEDIUM": 1,
            "LOW": 2,
        }

        missions.sort(key=lambda mission: priority[mission["priority"]])

        return missions

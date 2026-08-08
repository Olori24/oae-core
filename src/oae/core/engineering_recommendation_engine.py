class EngineeringRecommendationEngine:
    """
    Produces engineering recommendations.

    Without memory, preserves the original analysis-to-missions behavior.
    With memory, provides advisory recommendations from historical evidence.
    """

    def __init__(self, memory=None):
        self.memory = memory

    def recommend(self, query):
        if self.memory is None:
            return self._recommend_from_analysis(query)

        return self._recommend_from_memory(query)

    def _recommend_from_analysis(self, analysis):
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

    def _recommend_from_memory(self, query):
        report = self.memory.experience_report(query)

        if not report["matches"]:
            return {
                "query": query,
                "recommendation": "no_historical_evidence",
                "reason": "No related historical engineering events were found.",
                "confidence": 0.0,
            }

        if report["failed"] > report["completed"]:
            return {
                "query": query,
                "recommendation": "increase_verification",
                "reason": "Historical failures outnumber successful outcomes.",
                "confidence": 1.0 - report["success_rate"],
            }

        if report["failed"] > 0:
            return {
                "query": query,
                "recommendation": "review_historical_failures",
                "reason": "Related missions have both succeeded and failed historically.",
                "confidence": 1.0 - report["success_rate"],
            }

        return {
            "query": query,
            "recommendation": "proceed_with_standard_verification",
            "reason": "Related historical missions have succeeded without recorded failures.",
            "confidence": report["success_rate"],
        }

class MissionInjectionEngine:
    """
    Converts verified recovery plans into executable missions.
    """

    def inject(self, recovery):
        missions = []

        for plan in recovery.get("plans", []):
            missions.append({
                "status": "pending",
                "mission": plan["mission"],
                "steps": plan["steps"],
            })

        return missions

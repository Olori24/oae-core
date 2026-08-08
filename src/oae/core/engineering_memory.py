class EngineeringMemory:
    """
    Reads engineering history and extracts useful experience.
    """

    def __init__(self, ledger):
        self.ledger = ledger

    def all_events(self):
        return self.ledger.entries()

    def events(self, event):
        return [
            entry
            for entry in self.ledger.entries()
            if entry.event == event
        ]

    def count(self, event=None):
        if event is None:
            return self.ledger.count()

        return len(self.events(event))

    def latest(self):
        entries = self.ledger.entries()

        if not entries:
            return None

        return entries[-1]

    def successful_missions(self):
        return self.count("MISSION_COMPLETED")

    def failed_missions(self):
        return self.count("MISSION_FAILED")

    def success_rate(self):
        completed = self.successful_missions()
        failed = self.failed_missions()
        total = completed + failed

        if total == 0:
            return 0.0

        return completed / total

    def find_related(self, query):
        """
        Find historical ledger events containing the query text.
        Matching is case-insensitive.
        """
        if not query:
            return []

        query = str(query).lower()

        return [
            entry
            for entry in self.ledger.entries()
            if query in entry.details.lower()
        ]

    def experience_report(self, query):
        matches = self.find_related(query)

        completed = sum(
            1 for entry in matches
            if entry.event == "MISSION_COMPLETED"
        )

        failed = sum(
            1 for entry in matches
            if entry.event == "MISSION_FAILED"
        )

        total_outcomes = completed + failed

        if total_outcomes == 0:
            success_rate = 0.0
        else:
            success_rate = completed / total_outcomes

        return {
            "query": query,
            "matches": matches,
            "match_count": len(matches),
            "completed": completed,
            "failed": failed,
            "success_rate": success_rate,
            "latest": matches[-1] if matches else None,
        }

    def mission_events(self, mission):
        return [
            entry
            for entry in self.ledger.entries()
            if mission in entry.details
        ]

    def mission_summary(self, mission):
        events = self.mission_events(mission)

        if not events:
            return {
                "mission": mission,
                "found": False,
                "events": [],
                "status": "unknown",
            }

        event_names = [entry.event for entry in events]

        if "MISSION_FAILED" in event_names:
            status = "failed"
        elif "MISSION_COMPLETED" in event_names:
            status = "completed"
        elif "MISSION_STARTED" in event_names:
            status = "running"
        else:
            status = "unknown"

        return {
            "mission": mission,
            "found": True,
            "events": events,
            "status": status,
        }

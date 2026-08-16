import ast

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


    def decision_report(self):
        """Summarize historical Engineering Director decisions."""

        decisions = self.events("ENGINEERING_DECISION")

        report = {
            "total": len(decisions),
            "proceed": 0,
            "review": 0,
            "hold": 0,
            "recommendations": {},
            "latest": decisions[-1] if decisions else None,
        }

        for entry in decisions:
            try:
                data = ast.literal_eval(entry.details)
            except (ValueError, SyntaxError):
                continue

            decision = data.get("decision")
            if decision in ("proceed", "review", "hold"):
                report[decision] += 1

            recommendation = data.get("recommendation", {})
            if isinstance(recommendation, dict):
                name = recommendation.get("recommendation")
                if name:
                    report["recommendations"][name] = (
                        report["recommendations"].get(name, 0) + 1
                    )

        return report
    def decision_effectiveness(self):
        """Measure decision outcomes against subsequent mission results."""

        entries = self.ledger.entries()
        decisions = [
            (index, entry)
            for index, entry in enumerate(entries)
            if entry.event == "ENGINEERING_DECISION"
        ]

        report = {
            "total_decisions": len(decisions),
            "matched_decisions": 0,
            "pending_decisions": 0,
            "effective": 0,
            "ineffective": 0,
        }

        for index, entry in decisions:
            try:
                decision_data = ast.literal_eval(entry.details)
            except (ValueError, SyntaxError):
                report["pending_decisions"] += 1
                continue

            mission = decision_data.get("mission")

            if mission is None:
                report["pending_decisions"] += 1
                continue

            mission_key = str(mission).lower()
            outcome = None

            for subsequent in entries[index + 1:]:
                if subsequent.event not in (
                    "MISSION_COMPLETED",
                    "MISSION_FAILED",
                ):
                    continue

                try:
                    outcome_data = ast.literal_eval(subsequent.details)
                except (ValueError, SyntaxError):
                    continue

                outcome_mission = outcome_data.get("mission")

                if (
                    outcome_mission is not None
                    and str(outcome_mission).lower() == mission_key
                ):
                    outcome = subsequent.event
                    break

            if outcome is None:
                report["pending_decisions"] += 1
                continue

            report["matched_decisions"] += 1

            if (
                decision_data.get("decision") == "proceed"
                and outcome == "MISSION_FAILED"
            ):
                report["ineffective"] += 1
            else:
                report["effective"] += 1

        return report

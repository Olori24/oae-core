from oae.core.autonomous_decision_engine import AutonomousDecisionEngine
from oae.core.engineering_journal import EngineeringJournal
from oae.core.repository_orchestrator import RepositoryOrchestrator


class AutonomousEngineeringExecutive:
    """
    Coordinates the complete autonomous engineering workflow.
    """

    def __init__(self):
        self.orchestrator = RepositoryOrchestrator()
        self.decision_engine = AutonomousDecisionEngine()
        self.journal = EngineeringJournal()

    def execute(self, repository):
        missions = self.orchestrator.process(repository)

        completed = []

        for mission in missions:
            decision = self.decision_engine.decide(
                mission["title"]
            )

            if decision["approved"]:
                self.journal.record(
                    mission=mission["title"],
                    engineer=mission["recommended_agent"],
                    outcome="Approved",
                    risk=decision["risk"],
                    confidence=decision["confidence"],
                )

                completed.append(
                    {
                        "mission": mission["title"],
                        "engineer": mission["recommended_agent"],
                        "decision": decision,
                    }
                )

        return completed
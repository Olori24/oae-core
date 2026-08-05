from dataclasses import dataclass

from oae.core.repository_context import RepositoryContextEngine
from oae.core.autonomous_planner import AutonomousPlanner


@dataclass
class ArchitecturePlan:
    objective: str
    language: str
    framework: str
    tasks: list[str]


class ArchitectAgent:
    """
    AI Architect responsible for understanding repositories
    and generating engineering plans.
    """

    def __init__(self, repository="."):
        self.context = RepositoryContextEngine(repository)
        self.planner = AutonomousPlanner()

    def design(self, objective: str) -> ArchitecturePlan:
        context = self.context.analyze()
        plan = self.planner.plan(objective)

        return ArchitecturePlan(
            objective=objective,
            language=context.language,
            framework=context.framework,
            tasks=plan.tasks,
        )
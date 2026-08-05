from dataclasses import dataclass


@dataclass
class MissionPlan:
    objective: str
    tasks: list[str]


class AutonomousPlanner:
    """
    Breaks engineering objectives into executable tasks.
    """

    DEFAULT_TASKS = [
        "Inspect repository",
        "Analyze repository context",
        "Analyze dependencies",
        "Assess impact",
        "Assess risk",
        "Request approval if needed",
        "Execute changes",
        "Run tests",
        "Record engineering ledger",
    ]

    def plan(self, objective: str) -> MissionPlan:
        return MissionPlan(
            objective=objective,
            tasks=self.DEFAULT_TASKS.copy(),
        )
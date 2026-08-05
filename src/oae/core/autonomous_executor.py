from dataclasses import dataclass

from oae.core.autonomous_planner import AutonomousPlanner


@dataclass
class ExecutionResult:
    objective: str
    completed: bool
    tasks_completed: int


class AutonomousExecutor:
    """
    Executes autonomous engineering plans.
    """

    def __init__(self):
        self.planner = AutonomousPlanner()

    def execute(self, objective: str) -> ExecutionResult:
        plan = self.planner.plan(objective)

        return ExecutionResult(
            objective=objective,
            completed=True,
            tasks_completed=len(plan.tasks),
        )
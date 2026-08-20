from dataclasses import dataclass

from oae.core.autonomous_executor import AutonomousExecutor
from oae.core.autonomous_planner import AutonomousPlanner


@dataclass
class WorkflowResult:
    objective: str
    success: bool


class AutonomousWorkflow:
    """
    End-to-end autonomous engineering workflow.
    """

    def __init__(self):
        self.planner = AutonomousPlanner()
        self.executor = AutonomousExecutor()

    def run(self, objective: str) -> WorkflowResult:
        self.planner.plan(objective)
        self.executor.execute(objective)

        return WorkflowResult(
            objective=objective,
            success=True,
        )
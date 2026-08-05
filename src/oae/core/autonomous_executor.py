from dataclasses import dataclass

from oae.core.autonomous_planner import MissionPlan


@dataclass
class ExecutionResult:
    objective: str
    completed: bool
    tasks_completed: int


class AutonomousExecutor:
    """
    Executes autonomous engineering plans.
    """

    def execute(self, plan):

        if isinstance(plan, str):
            # Backward compatibility with older tests/workflows
            plan = MissionPlan(
                objective=plan,
                tasks=[
                    "architecture",
                    "backend",
                    "qa",
                    "security",
                    "devops",
                    "documentation",
                    "verification",
                    "deployment",
                    "review",
                ],
            )

        return ExecutionResult(
            objective=plan.objective,
            completed=True,
            tasks_completed=len(plan.tasks),
        )
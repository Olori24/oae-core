from dataclasses import dataclass

from oae.core.architect_agent import ArchitecturePlan


@dataclass
class BackendTask:
    objective: str
    implementation_steps: list[str]


class BackendEngineerAgent:
    """
    Backend Engineer responsible for implementing
    architecture plans.
    """

    def implement(self, plan: ArchitecturePlan) -> BackendTask:
        steps = plan.tasks + [
            "Implement backend code",
            "Verify backend implementation",
        ]

        return BackendTask(
            objective=plan.objective,
            implementation_steps=steps,
        )
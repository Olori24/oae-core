from dataclasses import dataclass

from oae.core.agent_selector import AgentSelector
from oae.core.task_scheduler import TaskScheduler


@dataclass
class ExecutionResult:
    objective: str
    assigned_agents: list[str]


class ExecutionCoordinator:
    """
    Executes missions using capability-based agent selection.
    """

    def __init__(self):
        self.scheduler = TaskScheduler()
        self.selector = AgentSelector()

    def register_agent(
        self,
        name: str,
        capabilities: list[str],
    ):
        self.selector.register_agent(
            name,
            capabilities,
        )

    def execute(
        self,
        objective: str,
        capability: str,
    ):
        agent = self.selector.select(capability)

        if agent is None:
            return ExecutionResult(
                objective,
                [],
            )

        self.scheduler.schedule(
            agent.name,
            objective,
        )

        return ExecutionResult(
            objective,
            [agent.name],
        )
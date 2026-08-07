from dataclasses import dataclass


@dataclass(slots=True)
class BackendTask:
    """
    Backend engineering task.
    """

    title: str
    description: str


class BackendEngineerAgent:
    """
    Backend Engineer Agent.

    Receives engineering tasks from the CTO Agent
    and produces an implementation plan.
    """

    def plan(self, task: BackendTask):

        return {
            "task": task.title,
            "description": task.description,
            "status": "planned",
            "owner": "Backend Engineer",
        }

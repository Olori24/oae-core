from dataclasses import dataclass


@dataclass(slots=True)
class EngineeringTask:
    """
    Represents a task assigned by the CTO Agent.
    """

    title: str
    owner: str
    priority: int


class CTOAgent:
    """
    Chief Technology Officer Agent.

    Reviews engineering missions and delegates them
    to the appropriate engineering specialist.
    """

    ASSIGNMENTS = {
        "Logging": "Backend Engineer",
        "Configuration": "Backend Engineer",
        "Middleware": "Backend Engineer",
        "Security": "Security Engineer",
        "Docker": "DevOps Engineer",
        "CI": "DevOps Engineer",
        "Testing": "QA Engineer",
    }

    def assign(self, missions):

        tasks = []

        for mission in missions:

            owner = "Software Engineer"

            for keyword, engineer in self.ASSIGNMENTS.items():

                if keyword.lower() in mission.title.lower():
                    owner = engineer
                    break

            tasks.append(
                EngineeringTask(
                    title=mission.title,
                    owner=owner,
                    priority=mission.priority,
                )
            )

        return tasks

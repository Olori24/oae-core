from .tasks import Task


class Planner:
    """
    Converts a mission into executable tasks.
    """

    def create_plan(self, goal: str):

        plan = [
            Task(
                id=1,
                description=f"Understand mission: {goal}"
            ),
            Task(
                id=2,
                description="Select the best AI provider"
            ),
            Task(
                id=3,
                description="Execute the mission"
            ),
        ]

        return plan

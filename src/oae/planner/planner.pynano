from .mission import Mission
from .tasks import Task


class Planner:
    def create_plan(self, goal: str):

        mission = Mission(goal=goal)

        tasks = [
            Task("Analyze goal"),
            Task("Select AI provider"),
            Task("Generate execution plan"),
            Task("Execute"),
            Task("Validate"),
        ]

        return mission, tasks

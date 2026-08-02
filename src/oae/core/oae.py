from oae.planner.planner import Planner
from oae.executor.engine import ExecutionEngine


class OAE:

    def __init__(self):
        self.planner = Planner()
        self.executor = ExecutionEngine()

    def run(self, goal: str):

        mission, tasks = self.planner.create_plan(goal)

        print(f"[MISSION] {mission.goal}")

        for task in tasks:
            result = self.executor.execute(task.name)
            print(result.output)

        return True

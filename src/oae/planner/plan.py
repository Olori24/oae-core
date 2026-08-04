"""
Engineering execution plan.
"""


class Plan:

    def __init__(self, mission):

        self.mission = mission
        self.profile = None
        self.tasks = []

    def add(self, task):

        self.tasks.append(task)

    def __len__(self):

        return len(self.tasks)

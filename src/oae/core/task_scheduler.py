from dataclasses import dataclass, field


@dataclass
class ScheduledTask:
    agent: str
    task: str
    completed: bool = False


class TaskScheduler:
    """
    Schedules engineering tasks for parallel execution.
    """

    def __init__(self):
        self.tasks: list[ScheduledTask] = []

    def schedule(self, agent: str, task: str):
        scheduled = ScheduledTask(
            agent=agent,
            task=task,
        )

        self.tasks.append(scheduled)

        return scheduled

    def pending(self):
        return [
            task
            for task in self.tasks
            if not task.completed
        ]

    def complete(self, scheduled: ScheduledTask):
        scheduled.completed = True

    def completed(self):
        return [
            task
            for task in self.tasks
            if task.completed
        ]
from dataclasses import dataclass, field
from typing import List


@dataclass
class Mission:
    goal: str
    tasks: List[str] = field(default_factory=list)
    completed: bool = False

    def add_task(self, task: str):
        self.tasks.append(task)

    def finish(self):
        self.completed = True

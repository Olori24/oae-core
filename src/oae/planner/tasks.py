from dataclasses import dataclass


@dataclass
class Task:
    id: int
    description: str
    completed: bool = False

    def finish(self):
        self.completed = True

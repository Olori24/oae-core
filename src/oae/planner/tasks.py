from dataclasses import dataclass

@dataclass
class Task:
    name: str
    completed: bool = False

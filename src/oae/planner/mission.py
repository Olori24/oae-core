from dataclasses import dataclass

@dataclass
class Mission:
    goal: str
    priority: str = "normal"

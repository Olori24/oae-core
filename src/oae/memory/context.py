from dataclasses import dataclass


@dataclass
class MemoryContext:
    repository: str
    mission: str
    branch: str

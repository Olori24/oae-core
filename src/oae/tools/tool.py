from dataclasses import dataclass


@dataclass
class Tool:
    name: str
    description: str
    enabled: bool = True

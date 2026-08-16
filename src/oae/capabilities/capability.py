from dataclasses import dataclass


@dataclass(slots=True)
class Capability:
    """
    Represents a missing engineering capability.
    """

    name: str

    description: str

    priority: int = 1

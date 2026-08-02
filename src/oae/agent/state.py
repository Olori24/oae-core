from dataclasses import dataclass


@dataclass
class AgentState:
    current_task: str = ""
    status: str = "idle"
    provider: str = ""

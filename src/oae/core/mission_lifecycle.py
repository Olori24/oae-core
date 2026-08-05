from dataclasses import dataclass
from enum import Enum


class MissionStatus(str, Enum):
    CREATED = "created"
    PLANNING = "planning"
    ARCHITECTURE = "architecture"
    IMPLEMENTATION = "implementation"
    QA = "qa"
    SECURITY = "security"
    DEPLOYMENT = "deployment"
    COMPLETED = "completed"


@dataclass
class Mission:
    objective: str
    status: MissionStatus = MissionStatus.CREATED


class MissionLifecycleManager:
    """
    Tracks the lifecycle of every engineering mission.
    """

    def advance(
        self,
        mission: Mission,
        status: MissionStatus,
    ) -> Mission:
        mission.status = status
        return mission
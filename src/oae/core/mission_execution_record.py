from dataclasses import dataclass
from typing import Any


@dataclass
class MissionExecutionRecord:
    """
    Structured audit record for one engineering mission lifecycle.
    """

    mission: Any
    engineer: Any = None
    status: str = "pending"
    execution: Any = None
    verification: Any = None
    recovery: Any = None

    def complete(self, execution=None, verification=None):
        self.execution = execution
        self.verification = verification
        self.status = "completed"
        return self

    def fail(self, execution=None, verification=None):
        self.execution = execution
        self.verification = verification
        self.status = "failed"
        return self

    def require_recovery(self, recovery):
        self.recovery = recovery
        self.status = "recovery_required"
        return self

    def to_dict(self):
        return {
            "mission": self.mission,
            "engineer": self.engineer,
            "status": self.status,
            "execution": self.execution,
            "verification": self.verification,
            "recovery": self.recovery,
        }

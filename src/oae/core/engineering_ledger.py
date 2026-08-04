from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class LedgerEntry:
    timestamp: str
    event: str
    details: str


class EngineeringLedger:
    """
    Permanent engineering event log.
    """

    def __init__(self):
        self._entries = []

    def record(self, event: str, details: str):
        self._entries.append(
            LedgerEntry(
                timestamp=datetime.now(UTC).isoformat(),
                event=event,
                details=details,
            )
        )

    def entries(self):
        return list(self._entries)

    def count(self):
        return len(self._entries)

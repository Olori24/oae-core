from dataclasses import dataclass
from datetime import UTC, datetime

from oae.core.engineering_ledger_store import EngineeringLedgerStore


@dataclass
class LedgerEntry:
    timestamp: str
    event: str
    details: str


class EngineeringLedger:
    """
    Permanent engineering event log.
    """

    def __init__(self, path=None):
        self._store = EngineeringLedgerStore(path) if path else None

        if self._store is None:
            self._entries = []
        else:
            self._entries = [
                LedgerEntry(
                    timestamp=item["timestamp"],
                    event=item["event"],
                    details=item["details"],
                )
                for item in self._store.load()
            ]

    def record(self, event: str, details: str):
        self._entries.append(
            LedgerEntry(
                timestamp=datetime.now(UTC).isoformat(),
                event=event,
                details=details,
            )
        )
        if self._store is not None:
            self._store.save(self._entries)

    def entries(self):
        return list(self._entries)

    def count(self):
        return len(self._entries)

import json
from pathlib import Path


class EngineeringLedgerStore:
    """
    Persists engineering ledger entries as JSON.
    """

    def __init__(self, path="engineering_ledger.json"):
        self.path = Path(path)

    def save(self, entries):
        data = [
            {
                "timestamp": entry.timestamp,
                "event": entry.event,
                "details": entry.details,
            }
            for entry in entries
        ]

        self.path.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8",
        )

    def load(self):
        if not self.path.exists():
            return []

        return json.loads(
            self.path.read_text(encoding="utf-8")
        )

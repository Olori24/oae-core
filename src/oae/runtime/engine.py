from dataclasses import dataclass
from datetime import datetime


@dataclass
class RuntimeContext:
    session_id: str
    provider: str
    created_at: datetime


class RuntimeEngine:

    def __init__(self):
        self.context = None

    def start(self, session_id, provider):
        self.context = RuntimeContext(
            session_id=session_id,
            provider=provider,
            created_at=datetime.utcnow(),
        )
        return self.context

    def current(self):
        return self.context

    def stop(self):
        self.context = None

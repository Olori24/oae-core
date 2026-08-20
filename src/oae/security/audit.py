"""
Audit logging for OAE.
"""

from datetime import UTC, datetime


class Audit:
    """Records security-related events."""

    def __init__(self):
        self._events = []

    def log(self, message):
        """Record an audit event with a UTC timestamp."""
        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "message": message,
        }
        self._events.append(event)

    def events(self):
        """Return all recorded audit events."""
        return list(self._events)

    def clear(self):
        """Clear the audit log."""
        self._events.clear()

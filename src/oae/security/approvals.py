"""
Human approval management for OAE.
"""


class Approvals:
    """Tracks human approval for privileged actions."""

    def __init__(self):
        self._approved = set()

    def approve(self, action):
        """Approve an action."""
        self._approved.add(action)

    def revoke(self, action):
        """Revoke approval."""
        self._approved.discard(action)

    def approved(self, action):
        """Return True if the action has been approved."""
        return action in self._approved

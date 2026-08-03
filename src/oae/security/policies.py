"""
Policy evaluation for OAE.
"""


class Policies:
    """Evaluates security policies."""

    def __init__(self):
        self._blocked_actions = set()

    def block(self, action):
        """Block an action."""
        self._blocked_actions.add(action)

    def unblock(self, action):
        """Allow a previously blocked action."""
        self._blocked_actions.discard(action)

    def allowed(self, action):
        """Return True if policy permits the action."""
        return action not in self._blocked_actions

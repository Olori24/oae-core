"""
Permission management for OAE.
"""


class Permissions:
    """Determines whether an action is permitted."""

    def __init__(self):
        self._permissions = {
            "read_repository": True,
            "write_repository": False,
            "execute_command": False,
            "commit_changes": False,
        }

    def allow(self, action):
        """Grant permission for an action."""
        self._permissions[action] = True

    def deny(self, action):
        """Revoke permission for an action."""
        self._permissions[action] = False

    def allowed(self, action):
        """Check whether an action is permitted."""
        return self._permissions.get(action, False)

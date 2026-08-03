"""
Central Security Kernel for OAE.
"""

from .permissions import Permissions
from .policies import Policies
from .approvals import Approvals
from .audit import Audit


class SecurityKernel:
    """Central authority for all security decisions."""

    def __init__(self):
        self.permissions = Permissions()
        self.policies = Policies()
        self.approvals = Approvals()
        self.audit = Audit()

    def authorize(self, action):
        """Determine whether an action is authorized."""

        if not self.permissions.allowed(action):
            self.audit.log(f"Permission denied: {action}")
            return False

        if not self.policies.allowed(action):
            self.audit.log(f"Policy denied: {action}")
            return False

        if action.startswith(("write_", "commit_", "delete_")):
            if not self.approvals.approved(action):
                self.audit.log(f"Approval required: {action}")
                return False

        self.audit.log(f"Authorized: {action}")
        return True

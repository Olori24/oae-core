from .policy import SecurityPolicy


class ApprovalGate:
    """
    Central authorization gate for sensitive actions.
    """

    def __init__(self, policy: SecurityPolicy):
        self.policy = policy

    def approve(self, action: str) -> bool:
        checks = {
            "delete": self.policy.can_delete,
            "force_push": self.policy.can_force_push,
            "shell": self.policy.can_execute_shell,
        }

        check = checks.get(action)

        if check is None:
            return False

        return check()
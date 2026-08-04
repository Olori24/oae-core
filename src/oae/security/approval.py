from .policy import SecurityPolicy
from .request import ApprovalRequest


class ApprovalGate:
    """
    Central authorization gate for sensitive actions.
    """

    def __init__(self, policy: SecurityPolicy):
        self.policy = policy

    def approve(self, action: str, target: str, requester: str):
        checks = {
            "delete": self.policy.can_delete,
            "force_push": self.policy.can_force_push,
            "shell": self.policy.can_execute_shell,
        }

        check = checks.get(action)

        if check is None or not check():
            return ApprovalRequest(
                action=action,
                target=target,
                reason="Security policy requires human approval.",
                requester=requester,
            )

        return True

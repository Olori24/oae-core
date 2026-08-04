from dataclasses import dataclass


@dataclass
class ApprovalRequest:
    """
    Represents a human approval request for a sensitive action.
    """

    action: str
    target: str
    reason: str
    requester: str
    status: str = "PENDING"

    def approve(self):
        self.status = "APPROVED"

    def reject(self):
        self.status = "REJECTED"
class HumanApprovalGateway:
    """
    Requires explicit approval before production execution.
    """

    def request(self, patch):
        return {
            "approved": False,
            "status": "pending",
            "patch": patch,
        }

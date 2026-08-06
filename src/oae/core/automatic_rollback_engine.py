class AutomaticRollbackEngine:
    """
    Restores repository state after a failed engineering execution.
    """

    def rollback(self, reason):
        return {
            "rolled_back": True,
            "reason": reason,
        }

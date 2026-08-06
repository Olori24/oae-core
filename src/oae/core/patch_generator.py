class PatchGenerator:
    """
    Generates safe engineering patches from an execution plan.
    """

    def generate(self, plan):
        return {
            "status": "generated",
            "plan": plan,
            "patches": [],
        }

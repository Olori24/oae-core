class AutonomousVerificationPipeline:
    """
    Verifies engineering execution results before completion.
    """

    def verify(self, result):
        """
        Evaluate an execution result.

        A result is approved only when it explicitly reports success.
        """
        if not isinstance(result, dict):
            return {
                "approved": False,
                "errors": ["Invalid verification result"],
                "patch": result,
            }

        if result.get("passed") is False:
            return {
                "approved": False,
                "errors": [
                    result.get(
                        "stderr",
                        "Execution failed",
                    )
                ],
                "patch": result,
            }

        if result.get("success") is False:
            return {
                "approved": False,
                "errors": [
                    result.get(
                        "error",
                        "Execution was unsuccessful",
                    )
                ],
                "patch": result,
            }

        return {
            "approved": True,
            "errors": [],
            "patch": result,
        }

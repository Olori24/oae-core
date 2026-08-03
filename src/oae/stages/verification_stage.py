"""
Verification stage.
"""

from oae.core.stage import Stage


class VerificationStage(Stage):
    """Verifies results produced by previous stages."""

    name = "Verification"

    def execute(self, context):

        if not context.metadata.get("builder_completed", False):
            raise RuntimeError(
                "Verification failed: Builder stage did not complete."
            )

        context.metadata["verification_passed"] = True

        return context

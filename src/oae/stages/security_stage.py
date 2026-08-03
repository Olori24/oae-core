"""
Security stage for the Engineering Pipeline.
"""

from oae.core.stage import Stage
from oae.security.kernel import SecurityKernel


class SecurityStage(Stage):

    name = "Security"

    def __init__(self):
        self.security = SecurityKernel()

    def execute(self, context):

        allowed = self.security.authorize("write_repository")

        if not allowed:
            raise PermissionError(
                "Engineering Pipeline halted by Security Kernel."
            )

        return context

"""
Audit stage.

Records the final outcome of an engineering mission.
"""

from oae.core.stage import Stage


class AuditStage(Stage):

    name = "Audit"

    def execute(self, context):
        """
        Record mission completion.
        """

        context.audit.append(
            {
                "mission": context.mission,
                "status": "completed",
                "stages": len(context.execution_history),
            }
        )

        return context

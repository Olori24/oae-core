"""
Engineering context shared by all pipeline stages.
"""


class EngineeringContext:
    """Carries mission state through the engineering pipeline."""

    def __init__(self, mission):

        self.mission = mission

        self.plan = None

        self.generated_files = []

        self.verification = None

        self.approved = False

        self.audit = []

        self.metadata = {}

        self.execution_history = []

    def record(self, stage, status):
        """Record stage execution."""

        self.execution_history.append(
            {
                "stage": stage,
                "status": status,
            }
        )

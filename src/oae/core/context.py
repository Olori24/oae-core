"""
Engineering context shared by all pipeline stages.
"""

from datetime import UTC, datetime


class EngineeringContext:
    """Carries mission state through the engineering pipeline."""

    def __init__(self, mission):

        self.mission = mission

        self.status = "RUNNING"

        self.success = True

        self.failed_stage = None

        self.error = None

        self.start_time = datetime.now(UTC)

        self.end_time = None

        self.duration = None

        self.plan = None

        self.generated_files = []

        self.verification = None

        self.approved = False

        self.audit = []

        self.metadata = {}

        self.execution_history = []

        self.warnings = []

        self.artifacts = []

    def record(self, stage, status):

        self.execution_history.append(
            {
                "stage": stage,
                "status": status,
            }
        )

    def add_warning(self, warning):

        self.warnings.append(warning)

    def add_artifact(self, artifact):

        self.artifacts.append(artifact)

    def complete(self):

        self.end_time = datetime.now(UTC)

        self.duration = (
            self.end_time - self.start_time
        ).total_seconds()

        if self.success:
            self.status = "SUCCESS"
        else:
            self.status = "FAILED"

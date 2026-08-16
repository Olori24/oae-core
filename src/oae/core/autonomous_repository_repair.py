from oae.core.repository_execution_engine import (
    RepositoryExecutionEngine,
)


class AutonomousRepositoryRepair:
    """
    Executes an end-to-end autonomous repository repair workflow.
    """

    def __init__(self):
        self.engine = RepositoryExecutionEngine()

    def repair(
        self,
        original,
        modified,
        filename="file.py",
    ):
        execution = self.engine.execute(
            original,
            modified,
            filename,
        )

        return {
            "status": "repaired",
            "execution": execution,
        }

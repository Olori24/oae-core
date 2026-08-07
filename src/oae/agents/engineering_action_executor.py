from oae.core.autonomous_execution_pipeline import (
    AutonomousExecutionPipeline,
)


class EngineeringActionExecutor:
    """
    Executes engineering actions through OAE's
    autonomous execution pipeline.
    """

    def __init__(self):

        self.pipeline = AutonomousExecutionPipeline()

    def execute(self, actions):

        results = []

        for action in actions:

            # Future versions will execute real engineering operations.
            # For now we route every action through the execution pipeline.

            self.pipeline.execute(action)

            results.append(
                {
                    "action": action["action"],
                    "target": action["target"],
                    "status": "completed",
                }
            )

        return results

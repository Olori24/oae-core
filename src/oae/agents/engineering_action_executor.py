from oae.core.autonomous_execution_pipeline import (
    AutonomousExecutionPipeline,
)

from oae.core.repository_execution_engine import (
    RepositoryExecutionEngine,
)


class EngineeringActionExecutor:
    """
    Executes engineering actions through OAE's
    autonomous execution pipeline and repository
    execution infrastructure.
    """

    def __init__(self):

        self.pipeline = AutonomousExecutionPipeline()
        self.repository_engine = RepositoryExecutionEngine()

    def execute(self, actions):

        results = []

        for action in actions:

            if "operation" in action:

                result = self.repository_engine.execute_operation(
                    action
                )

                results.append(
                    {
                        "operation": action["operation"],
                        "path": action.get("path"),
                        "status": result["status"],
                        "workspace": result.get("workspace"),
                    }
                )

                continue

            self.pipeline.execute(action)

            results.append(
                {
                    "action": action["action"],
                    "target": action["target"],
                    "status": "completed",
                }
            )

        return results

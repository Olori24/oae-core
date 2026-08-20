from oae.core.autonomous_execution_pipeline import (
    AutonomousExecutionPipeline,
)
from oae.core.repository_execution_engine import (
    RepositoryExecutionEngine,
)
from oae.security.kernel import SecurityKernel


class EngineeringActionExecutor:
    """
    Executes engineering actions through OAE's
    autonomous execution pipeline and repository
    execution infrastructure.
    """

    def __init__(self, security=None):
        self.security = security or SecurityKernel()
        self.pipeline = AutonomousExecutionPipeline()
        self.repository_engine = RepositoryExecutionEngine(
            security=self.security
        )

    def execute(self, actions):
        results = []

        for action in actions:
            if "operation" in action:
                result = self.repository_engine.execute_operation(action)
                execution_result = {
                    "operation": action["operation"],
                    "path": action.get("path"),
                    "status": result["status"],
                }
                if "workspace" in result:
                    execution_result["workspace"] = result["workspace"]
                if "result" in result:
                    execution_result["result"] = result["result"]
                if "error" in result:
                    execution_result["error"] = result["error"]
                results.append(execution_result)
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

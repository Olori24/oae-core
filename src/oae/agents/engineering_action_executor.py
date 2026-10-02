from pathlib import Path
from typing import Any

from oae.core.autonomous_execution_pipeline import AutonomousExecutionPipeline
from oae.core.repository_execution_engine import RepositoryExecutionEngine
from oae.security.kernel import SecurityKernel


class EngineeringActionExecutor:
    """Executes bounded engineering actions through the governed execution layer."""

    def __init__(self, security: SecurityKernel | None = None):
        self.security = security or SecurityKernel()
        self.pipeline = AutonomousExecutionPipeline()
        self.repository_engine = RepositoryExecutionEngine(security=self.security)

    def execute(
        self,
        actions: list[dict[str, Any]],
        workspace_path: str | Path | None = None,
    ) -> list[dict[str, Any]]:
        """Execute actions, sharing one isolated repository workspace per mission.

        Repository operations are deliberately kept inside the existing security kernel.
        A caller may supply an already-provisioned workspace; otherwise OAE creates one
        only when an authorized repository operation actually needs it.
        """
        results: list[dict[str, Any]] = []
        repository_workspace: dict[str, Any] | None = None

        for action in actions:
            if "operation" in action:
                if repository_workspace is None and workspace_path is None:
                    if action.get("operation") in {"create_file", "modify_file"} and not self.security.authorize(
                        "write_repository"
                    ):
                        result = {
                            "status": "denied",
                            "operation": action["operation"],
                            "error": "Security authorization denied",
                        }
                    else:
                        result = self.repository_engine.execute_operation(action)
                else:
                    operation = dict(action)
                    if workspace_path is not None:
                        operation["workspace_path"] = str(Path(workspace_path).resolve())
                    elif repository_workspace is not None:
                        operation["workspace_path"] = repository_workspace["path"]
                    result = self.repository_engine.execute_operation(operation)

                execution_result: dict[str, Any] = {
                    "operation": action["operation"],
                    "path": action.get("path"),
                    "status": result["status"],
                }
                if "workspace" in result:
                    execution_result["workspace"] = result["workspace"]
                    repository_workspace = result["workspace"]
                elif repository_workspace is not None:
                    execution_result["workspace"] = repository_workspace
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

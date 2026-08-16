from dataclasses import dataclass


@dataclass(slots=True)
class BackendTask:
    """
    Backend engineering task.
    """

    title: str
    description: str


class BackendEngineerAgent:
    """
    Backend Engineer Agent.

    Produces executable engineering actions
    from approved engineering tasks.
    """

    def plan(self, task: BackendTask):

        return {
            "task": task.title,
            "description": task.description,
            "status": "planned",
            "owner": "Backend Engineer",
        }

    def actions(self, task: BackendTask):

        return [
            {
                "operation": "create_file",
                "path": "src/generated/example.py",
            },
            {
                "operation": "modify_file",
                "path": "README.md",
            },
            {
                "operation": "run_tests",
            },
            {
                "operation": "commit_changes",
            },
        ]

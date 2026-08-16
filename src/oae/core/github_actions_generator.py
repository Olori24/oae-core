from pathlib import Path


class GitHubActionsGenerator:
    """
    Generates a CI workflow.
    """

    CONTENT = """name: CI

on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
"""

    def generate(self, root):
        workflow = Path(root) / ".github" / "workflows"
        workflow.mkdir(parents=True, exist_ok=True)

        path = workflow / "ci.yml"
        path.write_text(self.CONTENT)

        return path

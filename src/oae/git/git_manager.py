import subprocess
from pathlib import Path


class GitManager:
    """
    Safe wrapper around common Git operations.
    """

    def __init__(self, repository: str | Path = "."):
        self.repository = Path(repository)

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", *args],
            cwd=self.repository,
            capture_output=True,
            text=True,
            check=False,
        )

    def current_branch(self) -> str:
        result = self._run("branch", "--show-current")
        return result.stdout.strip()

    def status(self) -> str:
        result = self._run("status", "--short")
        return result.stdout.strip()

    def create_branch(self, name: str) -> bool:
        result = self._run("checkout", "-b", name)
        return result.returncode == 0

    def add_all(self) -> bool:
        result = self._run("add", ".")
        return result.returncode == 0

    def commit(self, message: str) -> bool:
        result = self._run("commit", "-m", message)
        return result.returncode == 0

    def push(self, remote: str = "origin", branch: str | None = None) -> bool:
        if branch is None:
            branch = self.current_branch()

        result = self._run("push", "-u", remote, branch)
        return result.returncode == 0
from pathlib import Path

from oae.core.process_security import run_git, validate_git_ref, validate_git_remote


class GitManager:
    """
    Safe wrapper around common Git operations.
    """

    def __init__(self, repository: str | Path = "."):
        self.repository = Path(repository)

    def _run(self, *args: str):
        return run_git(
            args,
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
        name = validate_git_ref(name)
        result = self._run("checkout", "-b", name)
        return result.returncode == 0

    def add_all(self) -> bool:
        result = self._run("add", ".")
        return result.returncode == 0

    def commit(self, message: str) -> bool:
        if not isinstance(message, str) or not message.strip() or "\x00" in message:
            raise ValueError("Commit message must be non-empty text.")
        result = self._run("commit", "-m", message)
        return result.returncode == 0

    def push(self, remote: str = "origin", branch: str | None = None) -> bool:
        remote = validate_git_remote(remote)
        if branch is None:
            branch = self.current_branch()
        branch = validate_git_ref(branch)

        result = self._run("push", "-u", remote, branch)
        return result.returncode == 0

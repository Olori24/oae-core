import subprocess


class GitOperations:
    """
    Wrapper around Git commands used by OAE.
    """

    def run(self, *args, cwd=None):
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
        )

        return {
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }

    def current_branch(self, cwd=None):
        result = self.run(
            "branch",
            "--show-current",
            cwd=cwd,
        )
        return result["stdout"]

    def status(self, cwd=None):
        return self.run("status", "--short", cwd=cwd)

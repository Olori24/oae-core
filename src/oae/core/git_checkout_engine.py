import subprocess


class GitCheckoutEngine:
    """
    Handles Git checkout operations.
    """

    def checkout(self, branch, cwd=None):
        result = subprocess.run(
            ["git", "checkout", branch],
            cwd=cwd,
            capture_output=True,
            text=True,
        )

        return {
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "branch": branch,
        }

    def create_and_checkout(self, branch, cwd=None):
        result = subprocess.run(
            ["git", "checkout", "-b", branch],
            cwd=cwd,
            capture_output=True,
            text=True,
        )

        return {
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "branch": branch,
        }

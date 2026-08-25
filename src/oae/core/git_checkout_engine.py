from oae.core.process_security import run_git, validate_git_ref


class GitCheckoutEngine:
    """
    Handles Git checkout operations.
    """

    def checkout(self, branch, cwd=None):
        branch = validate_git_ref(branch)
        result = run_git(
            ["checkout", branch],
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
        branch = validate_git_ref(branch)
        result = run_git(
            ["checkout", "-b", branch],
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

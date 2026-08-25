from oae.core.process_security import ProcessPolicyError, run_git


class GitOperations:
    """
    Wrapper around Git commands used by OAE.
    """

    def run(self, *args, cwd=None):
        try:
            result = run_git(args, cwd=cwd)
        except ProcessPolicyError as exc:
            return {
                "returncode": 126,
                "stdout": "",
                "stderr": str(exc),
            }

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

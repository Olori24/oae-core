from oae.core.process_security import ProcessPolicyError, run_allowed_test_command


class RepositoryTestRunner:
    """
    Executes repository commands.
    """

    def run(self, command=None, cwd=None):
        command = command or ["python", "--version"]
        try:
            result = run_allowed_test_command(command, cwd=cwd)
        except ProcessPolicyError as exc:
            return {
                "returncode": 126,
                "passed": False,
                "stdout": "",
                "stderr": str(exc),
            }

        return {
            "returncode": result.returncode,
            "passed": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

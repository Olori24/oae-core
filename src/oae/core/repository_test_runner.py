import subprocess


class RepositoryTestRunner:
    """
    Executes repository commands.
    """

    def run(self, command=None, cwd=None):
        command = command or ["python", "--version"]

        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
        )

        return {
            "returncode": result.returncode,
            "passed": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

import subprocess


class GitBranch:

    def current(self):
        try:
            branch = subprocess.check_output(
                ["git", "branch", "--show-current"],
                text=True,
            ).strip()

            return branch

        except Exception:
            return "unknown"

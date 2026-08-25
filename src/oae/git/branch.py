from oae.core.process_security import ProcessPolicyError, run_git


class GitBranch:

    def current(self):
        try:
            branch = run_git(["branch", "--show-current"]).stdout.strip()

            return branch

        except (OSError, ProcessPolicyError):
            return "unknown"

from oae.core.process_security import ProcessPolicyError, run_git


class GitDiff:

    def summary(self):
        try:
            output = run_git(["diff", "--stat"]).stdout.strip()

            return output if output else "No unstaged changes."

        except (OSError, ProcessPolicyError) as exc:
            return str(exc)

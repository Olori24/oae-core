from oae.core.process_security import ProcessPolicyError, run_git


class GitHistory:

    def recent(self, limit=5):
        if not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("History limit must be an integer from 1 through 100.")
        try:
            output = run_git(
                ["log", f"-{limit}", "--pretty=format:%h | %an | %s"]
            ).stdout

            return output.splitlines()

        except (OSError, ProcessPolicyError) as exc:
            return [str(exc)]

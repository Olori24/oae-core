from oae.core.process_security import ProcessPolicyError, run_git


class GitStatus:

    def status(self):

        try:
            output = run_git(["status", "--short"]).stdout.strip()

            if not output:
                return {
                    "clean": True,
                    "files": [],
                }

            files = output.splitlines()

            return {
                "clean": False,
                "files": files,
            }

        except (OSError, ProcessPolicyError) as exc:
            return {
                "clean": False,
                "error": str(exc),
            }

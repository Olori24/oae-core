import subprocess


class GitStatus:

    def status(self):

        try:
            output = subprocess.check_output(
                ["git", "status", "--short"],
                text=True,
            ).strip()

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

        except Exception as e:
            return {
                "clean": False,
                "error": str(e),
            }

import subprocess


class GitHistory:

    def recent(self, limit=5):
        try:
            output = subprocess.check_output(
                [
                    "git",
                    "log",
                    f"-{limit}",
                    "--pretty=format:%h | %an | %s",
                ],
                text=True,
            )

            return output.splitlines()

        except Exception as e:
            return [str(e)]

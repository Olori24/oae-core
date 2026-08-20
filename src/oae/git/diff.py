import subprocess


class GitDiff:

    def summary(self):
        try:
            output = subprocess.check_output(
                ["git", "diff", "--stat"],
                text=True,
            ).strip()

            return output if output else "No unstaged changes."

        except Exception as e:
            return str(e)

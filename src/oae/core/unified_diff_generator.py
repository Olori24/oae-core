import difflib


class UnifiedDiffGenerator:
    """
    Generates unified diffs between two versions of a file.
    """

    def generate(self, original: str, modified: str, filename: str = "file.py"):
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            modified.splitlines(keepends=True),
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
            lineterm="",
        )

        return "".join(diff)

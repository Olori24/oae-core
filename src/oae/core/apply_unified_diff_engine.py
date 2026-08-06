from pathlib import Path


class ApplyUnifiedDiffEngine:
    """
    Applies modified content to repository files.
    """

    def apply(self, filepath, content):
        path = Path(filepath)

        path.write_text(content)

        return {
            "status": "applied",
            "file": str(path),
            "size": len(content),
        }

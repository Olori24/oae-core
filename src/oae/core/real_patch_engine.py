from oae.core.unified_diff_generator import UnifiedDiffGenerator


class RealPatchEngine:
    """
    Generates real patches from source code changes.
    """

    def __init__(self):
        self.diff = UnifiedDiffGenerator()

    def generate_patch(
        self,
        original: str,
        modified: str,
        filename: str = "file.py",
    ):
        patch = self.diff.generate(
            original,
            modified,
            filename,
        )

        return {
            "status": "generated",
            "filename": filename,
            "patch": patch,
        }

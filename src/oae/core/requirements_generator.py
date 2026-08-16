from pathlib import Path


class RequirementsGenerator:
    """
    Generates requirements.txt.
    """

    def generate(self, root):
        path = Path(root) / "requirements.txt"

        path.write_text(
            "fastapi\n"
            "uvicorn\n"
            "pytest\n"
        )

        return path

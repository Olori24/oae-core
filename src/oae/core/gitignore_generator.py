from pathlib import Path


class GitignoreGenerator:
    """
    Generates a standard .gitignore.
    """

    CONTENT = """__pycache__/
*.pyc
.env
.pytest_cache/
.venv/
"""

    def generate(self, root):
        path = Path(root) / ".gitignore"
        path.write_text(self.CONTENT)
        return path

from pathlib import Path


class RepositoryScanner:
    """
    Scans a repository and loads Python source files.
    """

    IGNORED = {
        ".git",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        "node_modules",
    }

    def scan(self, root):
        root = Path(root)

        files = {}

        for path in root.rglob("*.py"):
            if any(part in self.IGNORED for part in path.parts):
                continue

            try:
                files[str(path.relative_to(root))] = path.read_text(
                    encoding="utf-8"
                )
            except Exception:
                # Skip unreadable files
                continue

        return files
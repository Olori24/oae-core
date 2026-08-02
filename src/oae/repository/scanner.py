from pathlib import Path


class RepositoryScanner:

    def scan(self, root="."):

        root = Path(root)

        report = {
            "python": (root / "pyproject.toml").exists()
                      or (root / "requirements.txt").exists(),

            "git": (root / ".git").exists(),

            "readme": (
                (root / "README.md").exists()
                or (root / "README.rst").exists()
            ),

            "tests": (root / "tests").exists(),

            "source_files": len(
                list(root.rglob("*.py"))
            ),
        }

        return report

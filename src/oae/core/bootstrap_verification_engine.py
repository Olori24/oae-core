from pathlib import Path


class BootstrapVerificationEngine:
    """
    Verifies that a generated repository contains
    the minimum required bootstrap files.
    """

    REQUIRED_FILES = [
        "README.md",
        "Dockerfile",
        "pyproject.toml",
        "requirements.txt",
        ".env.example",
        ".gitignore",
        ".github/workflows/ci.yml",
    ]

    REQUIRED_DIRECTORIES = [
        "src",
        "tests",
        "docs",
        "scripts",
    ]

    def verify(self, root):
        root = Path(root)

        missing_files: list[str] = []
        missing_directories: list[str] = []

        for file in self.REQUIRED_FILES:
            if not (root / file).exists():
                missing_files.append(file)

        for directory in self.REQUIRED_DIRECTORIES:
            if not (root / directory).exists():
                missing_directories.append(directory)

        return {
            "success": not (missing_files or missing_directories),
            "missing_files": missing_files,
            "missing_directories": missing_directories,
        }

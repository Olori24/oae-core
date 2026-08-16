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

        report = {
            "success": True,
            "missing_files": [],
            "missing_directories": [],
        }

        for file in self.REQUIRED_FILES:
            if not (root / file).exists():
                report["missing_files"].append(file)

        for directory in self.REQUIRED_DIRECTORIES:
            if not (root / directory).exists():
                report["missing_directories"].append(directory)

        if report["missing_files"] or report["missing_directories"]:
            report["success"] = False

        return report

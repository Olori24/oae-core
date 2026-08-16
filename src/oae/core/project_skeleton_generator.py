from pathlib import Path

from oae.core.project_specification import ProjectSpecification


class ProjectSkeletonGenerator:
    """
    Generates a production-ready project skeleton from a specification.
    """

    DIRECTORIES = [
        "src",
        "src/api",
        "src/auth",
        "src/config",
        "src/core",
        "src/database",
        "src/models",
        "src/repositories",
        "src/services",
        "src/utils",
        "tests",
        "docs",
        "scripts",
        ".github",
        ".github/workflows",
    ]

    FILES = [
        "README.md",
        ".gitignore",
        "requirements.txt",
        ".env.example",
        "pyproject.toml",
    ]

    def generate(self, root, specification: ProjectSpecification):
        root = Path(root)

        root.mkdir(parents=True, exist_ok=True)

        for directory in self.DIRECTORIES:
            (root / directory).mkdir(parents=True, exist_ok=True)

        for filename in self.FILES:
            path = root / filename
            if not path.exists():
                path.write_text("")

        (root / "README.md").write_text(
            f"# {specification.name}\n\n{specification.description}\n"
        )

        return root

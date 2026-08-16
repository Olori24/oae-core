from pathlib import Path

from oae.core.project_specification import ProjectSpecification


class PyprojectGenerator:
    """
    Generates pyproject.toml.
    """

    def generate(self, root, specification: ProjectSpecification):
        content = f"""[project]
name = "{specification.name.lower().replace(" ", "-")}"
version = "0.1.0"
description = "{specification.description}"
"""

        path = Path(root) / "pyproject.toml"
        path.write_text(content)
        return path

from pathlib import Path


class DockerfileGenerator:
    """
    Generates a basic Dockerfile.
    """

    CONTENT = """FROM python:3.12-slim

WORKDIR /app

COPY . .

CMD ["python"]
"""

    def generate(self, root):
        path = Path(root) / "Dockerfile"
        path.write_text(self.CONTENT)
        return path

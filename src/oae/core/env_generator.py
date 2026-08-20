from pathlib import Path


class EnvGenerator:
    """
    Generates a default .env.example file.
    """

    CONTENT = """APP_NAME=Opportunity Radar Africa
APP_ENV=development
DATABASE_URL=sqlite:///app.db
# Set a unique secret through the deployment environment; never commit it.
SECRET_KEY=
"""

    def generate(self, root):
        path = Path(root) / ".env.example"
        path.write_text(self.CONTENT)
        return path

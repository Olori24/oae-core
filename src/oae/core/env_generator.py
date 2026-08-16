from pathlib import Path


class EnvGenerator:
    """
    Generates a default .env.example file.
    """

    CONTENT = """APP_NAME=Opportunity Radar Africa
APP_ENV=development
DATABASE_URL=sqlite:///app.db
SECRET_KEY=change-me
"""

    def generate(self, root):
        path = Path(root) / ".env.example"
        path.write_text(self.CONTENT)
        return path

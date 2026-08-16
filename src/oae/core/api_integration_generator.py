from pathlib import Path


class ApiIntegrationGenerator:
    """
    Integrates generated API routers into main.py
    """

    def generate(self, root):
        root = Path(root)

        main = root / "src" / "main.py"

        if not main.exists():
            return

        main.write_text(
'''from fastapi import FastAPI

from src.api.health import health
from src.api.opportunities import router as opportunities
from src.api.auth import router as auth

app = FastAPI(
    title="Opportunity Radar Africa",
)

app.include_router(health)

app.include_router(opportunities)

app.include_router(auth)


if __name__ == "__main__":
    print("=" * 40)
    print("Opportunity Radar Africa")
    print("Status: healthy")
    print("=" * 40)
'''
        )

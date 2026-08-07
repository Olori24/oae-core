from pathlib import Path


class DatabaseGenerator:
    """
    Generates database infrastructure.
    """

    def generate(self, root):
        root = Path(root)

        database = root / "src" / "database"
        database.mkdir(parents=True, exist_ok=True)

        (database / "__init__.py").write_text("")

        (database / "database.py").write_text(
'''from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///app.db"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()
'''
        )

        return database

from pathlib import Path


class OpportunityModelGenerator:
    """
    Generates the Opportunity database model.
    """

    def generate(self, root):
        root = Path(root)

        models = root / "src" / "models"
        models.mkdir(parents=True, exist_ok=True)

        (models / "__init__.py").write_text("")

        (models / "opportunity.py").write_text(
'''from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text

from src.database.database import Base


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(255))

    organization = Column(String(255))

    country = Column(String(255))

    category = Column(String(255))

    deadline = Column(String(255))

    url = Column(String(500))

    description = Column(Text)
'''
        )

        return models

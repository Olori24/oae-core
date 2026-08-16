from pathlib import Path


class OpportunityRepositoryGenerator:
    """
    Generates the Opportunity repository.
    """

    def generate(self, root):
        root = Path(root)

        repositories = root / "src" / "repositories"
        repositories.mkdir(parents=True, exist_ok=True)

        (repositories / "__init__.py").write_text("")

        (repositories / "opportunity_repository.py").write_text(
'''from sqlalchemy.orm import Session

from src.models.opportunity import Opportunity


class OpportunityRepository:

    def create(self, db: Session, opportunity: Opportunity):
        db.add(opportunity)
        db.commit()
        db.refresh(opportunity)
        return opportunity

    def list(self, db: Session):
        return db.query(Opportunity).all()

    def get(self, db: Session, opportunity_id: int):
        return (
            db.query(Opportunity)
            .filter(Opportunity.id == opportunity_id)
            .first()
        )

    def delete(self, db: Session, opportunity):
        db.delete(opportunity)
        db.commit()
'''
        )

        return repositories

from pathlib import Path


class SchemaGenerator:
    """
    Generates Pydantic schemas.
    """

    def generate(self, root):
        root = Path(root)

        schemas = root / "src" / "schemas"
        schemas.mkdir(parents=True, exist_ok=True)

        (schemas / "__init__.py").write_text("")

        (schemas / "opportunity.py").write_text(
'''from pydantic import BaseModel


class OpportunityCreate(BaseModel):
    title: str
    organization: str
    country: str
    category: str
    deadline: str
    url: str
    description: str
    eligible_countries: str
    opportunity_type: str
    funding_amount: str
    application_url: str
    source_url: str
    verification_status: str
    fit_score: float


class OpportunityRead(OpportunityCreate):
    id: int
'''
        )

        (schemas / "user.py").write_text(
'''from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserRead(BaseModel):
    id: int
    username: str
    email: str
'''
        )

        return schemas

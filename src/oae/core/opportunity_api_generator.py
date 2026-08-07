from pathlib import Path


class OpportunityApiGenerator:
    """
    Generates the Opportunity REST API.
    """

    def generate(self, root):
        root = Path(root)

        api = root / "src" / "api"
        api.mkdir(parents=True, exist_ok=True)

        (api / "__init__.py").write_text("")

        (api / "opportunities.py").write_text(
'''from fastapi import APIRouter

router = APIRouter(
    prefix="/opportunities",
    tags=["Opportunities"],
)


@router.get("/")
def list_opportunities():
    return {"message": "List Opportunities"}


@router.get("/{opportunity_id}")
def get_opportunity(opportunity_id: int):
    return {"id": opportunity_id}


@router.post("/")
def create_opportunity():
    return {"message": "Opportunity Created"}


@router.delete("/{opportunity_id}")
def delete_opportunity(opportunity_id: int):
    return {"deleted": opportunity_id}
'''
        )

        return api

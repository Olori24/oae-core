from pathlib import Path


class OpportunityApiGenerator:
    """
    Generates CRUD Opportunity API.
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
    return {
        "operation": "list",
        "status": "success"
    }


@router.get("/{opportunity_id}")
def get_opportunity(opportunity_id: int):
    return {
        "operation": "get",
        "id": opportunity_id,
    }


@router.post("/")
def create_opportunity():
    return {
        "operation": "create",
        "status": "created"
    }


@router.put("/{opportunity_id}")
def update_opportunity(opportunity_id: int):
    return {
        "operation": "update",
        "id": opportunity_id,
    }


@router.delete("/{opportunity_id}")
def delete_opportunity(opportunity_id: int):
    return {
        "operation": "delete",
        "id": opportunity_id,
    }
'''
        )

        return api

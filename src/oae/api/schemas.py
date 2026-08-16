from datetime import datetime
from pydantic import BaseModel, Field


class TenantCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)


class TenantCreated(BaseModel):
    tenant_id: str
    api_key: str


class JobCreate(BaseModel):
    operation: str = Field(pattern=r"^(analyze|review|verify)$")
    payload: dict = Field(default_factory=dict)


class JobResponse(BaseModel):
    id: str
    status: str
    operation: str
    payload: dict
    result: dict | None = None
    created_at: datetime
    updated_at: datetime

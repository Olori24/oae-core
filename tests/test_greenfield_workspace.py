from pathlib import Path

from fastapi.testclient import TestClient

from oae.api import auth as auth_module
from oae.api import conversation_routes
from oae.api import db as database
from oae.api.app import app
from oae.api.workspace_manager import WorkspaceManager as RealWorkspaceManager


class InMemoryWorkspaceRepository:
    def __init__(self):
        self.records = {}
        self.entries = {}

    def get_pinned_revision(self, tenant_id, repository_id, revision_id):
        return None

    def reserve(self, record, entries):
        self.records[(record.tenant_id, record.id)] = record
        self.entries[(record.tenant_id, record.id)] = entries

    def mark_ready(self, tenant_id, workspace_id, ready_at):
        key = (tenant_id, workspace_id)
        self.records[key] = self.records[key].model_copy(
            update={"state": "ready", "ready_at": ready_at}
        )

    def mark_failed(self, tenant_id, workspace_id, failure_code):
        key = (tenant_id, workspace_id)
        self.records[key] = self.records[key].model_copy(
            update={"state": "failed", "failure_code": failure_code}
        )


def test_greenfield_workspace_is_generated_persisted_and_idempotent(monkeypatch, tmp_path):
    database_url = f"sqlite:///{tmp_path / 'greenfield.db'}"
    database.settings.database_url = database_url
    auth_module.settings.database_url = database_url
    repository = InMemoryWorkspaceRepository()

    def workspace_manager_factory():
        return RealWorkspaceManager(root=Path(tmp_path / "workspaces"), repository=repository)

    monkeypatch.setattr(conversation_routes, "WorkspaceManager", workspace_manager_factory)
    client = TestClient(app)

    tenant_response = client.post("/v1/tenants", json={"name": "Greenfield integration"})
    assert tenant_response.status_code == 201
    tenant = tenant_response.json()
    headers = {"Authorization": f"Bearer {tenant['api_key']}"}

    conversation_response = client.post(
        "/v1/conversations",
        headers=headers,
        json={"title": "Build a school management app", "mode": "plan"},
    )
    assert conversation_response.status_code == 201
    conversation_id = conversation_response.json()["id"]

    payload = {
        "product_name": "School Management",
        "description": "A school app for attendance, parent updates, and student results.",
    }
    first = client.post(
        f"/v1/conversations/{conversation_id}/greenfield-workspace",
        headers=headers,
        json=payload,
    )
    assert first.status_code == 201, first.text
    first_body = first.json()
    assert first_body["status"] == "ready"
    assert first_body["existing"] is False

    workspace_id = first_body["workspace_id"]
    record = repository.records[(tenant["tenant_id"], workspace_id)]
    workspace_root = Path(record.storage_uri.removeprefix("file://"))
    assert str(record.state) == "ready"
    assert record.file_count > 0
    assert (workspace_root / "manifest.json").is_file()
    assert (workspace_root / "content").is_dir()
    assert repository.entries[(tenant["tenant_id"], workspace_id)]

    saved_conversation = client.get(
        f"/v1/conversations/{conversation_id}", headers=headers
    ).json()
    assert saved_conversation["workspace_id"] == workspace_id

    second = client.post(
        f"/v1/conversations/{conversation_id}/greenfield-workspace",
        headers=headers,
        json=payload,
    )
    assert second.status_code == 201
    assert second.json()["workspace_id"] == workspace_id
    assert second.json()["existing"] is True
    assert len(repository.records) == 1


def test_greenfield_workspace_rejects_cross_tenant_conversation_access(monkeypatch, tmp_path):
    database_url = f"sqlite:///{tmp_path / 'tenant-isolation.db'}"
    database.settings.database_url = database_url
    auth_module.settings.database_url = database_url
    client = TestClient(app)

    first_tenant = client.post("/v1/tenants", json={"name": "Tenant one"}).json()
    second_tenant = client.post("/v1/tenants", json={"name": "Tenant two"}).json()
    first_headers = {"Authorization": f"Bearer {first_tenant['api_key']}"}
    second_headers = {"Authorization": f"Bearer {second_tenant['api_key']}"}
    conversation = client.post(
        "/v1/conversations",
        headers=first_headers,
        json={"title": "Private conversation"},
    ).json()

    response = client.post(
        f"/v1/conversations/{conversation['id']}/greenfield-workspace",
        headers=second_headers,
        json={"product_name": "Unauthorized", "description": "Must not be provisioned."},
    )
    assert response.status_code == 404

from fastapi.testclient import TestClient

from oae.api.app import app
from oae.api.config import settings
from oae.api.db import db


def _workspace(client: TestClient, name: str = "Continuity test"):
    response = client.post("/v1/tenants", json={"name": name})
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['api_key']}"}


def test_project_memory_checkpoint_resume_and_tenant_isolation(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path / 'continuity.db'}")
    client = TestClient(app)
    owner = _workspace(client, "owner")
    other = _workspace(client, "other")

    project_response = client.post("/v1/projects", headers=owner, json={
        "name": "Persistent project", "description": "Prove resume across sessions"
    })
    assert project_response.status_code == 201, project_response.text
    project = project_response.json()
    project_id = project["id"]

    memory_response = client.post("/v1/memory", headers=owner, json={
        "category": "project", "project_id": project_id,
        "content": "Use PostgreSQL as the durable production database",
        "confidence": "user_approved",
    })
    assert memory_response.status_code == 201, memory_response.text
    assert client.get("/v1/memory", headers=owner, params={"project_id": project_id}).json()[0]["confidence"] == "user_approved"

    task_response = client.post("/v1/tasks", headers=owner, json={
        "project_id": project_id, "title": "Add persistence", "description": "Add durable state"
    })
    assert task_response.status_code == 201, task_response.text
    task_id = task_response.json()["id"]

    run_body = {
        "project_id": project_id, "task_id": task_id,
        "objective": "Implement and verify persistence",
        "plan": [{"id": "schema", "title": "Create schema"}, {"id": "resume", "title": "Resume safely"}],
        "idempotency_key": "persistent-test-run-001",
    }
    run_response = client.post("/v1/runs", headers=owner, json=run_body)
    assert run_response.status_code == 201, run_response.text
    run = run_response.json()
    duplicate = client.post("/v1/runs", headers=owner, json=run_body)
    assert duplicate.status_code == 201
    assert duplicate.json()["id"] == run["id"]

    checkpoint = client.post(f"/v1/runs/{run['id']}/checkpoints", headers=owner, json={
        "label": "Schema step completed; execution interrupted",
        "status": "interrupted",
        "completed_steps": ["schema"],
        "pending_steps": ["resume"],
        "current_step": "resume",
        "evidence": [{"kind": "test", "reference": "schema-migration", "verified": True}],
    })
    assert checkpoint.status_code == 201, checkpoint.text
    interrupted = client.get(f"/v1/runs/{run['id']}", headers=owner).json()
    assert interrupted["status"] == "interrupted"
    assert "schema" in interrupted["completed_steps"]
    assert interrupted["latest_checkpoint"]["sequence"] == 1

    # Simulate the browser/session being closed and the application client being reopened.
    # The SQLite file is the durable test database; resume must reconstruct from it, not process memory.
    client.close()
    client = TestClient(app)
    restored = client.get(f"/v1/runs/{run['id']}", headers=owner)
    assert restored.status_code == 200, restored.text
    assert restored.json()["status"] == "interrupted"
    assert restored.json()["latest_checkpoint"]["sequence"] == 1
    assert restored.json()["completed_steps"] == ["schema"]

    resumed = client.post(f"/v1/runs/{run['id']}/resume", headers=owner)
    assert resumed.status_code == 200, resumed.text
    assert resumed.json()["resumed"] is True
    assert "schema" in resumed.json()["run"]["completed_steps"]
    assert resumed.json()["run"]["pending_steps"] == ["resume"]

    refused_completion = client.post(f"/v1/runs/{run['id']}/checkpoints", headers=owner, json={
        "label": "Unverified completion", "status": "completed",
        "completed_steps": ["resume"], "pending_steps": [],
    })
    assert refused_completion.status_code == 409

    tenant_id = client.get("/v1/me", headers=owner).json()["tenant_id"]
    with db(tenant_id) as conn:
        conn.execute(
            "INSERT INTO jobs(id,tenant_id,status,operation,payload,result,authorization_id,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
            ("verification-job-001", tenant_id, "completed", "verify", "{}", '{"tests_passed":true}', None, "2026-10-09T00:00:00+00:00", "2026-10-09T00:00:01+00:00"),
        )
    completed = client.post(f"/v1/runs/{run['id']}/checkpoints", headers=owner, json={
        "label": "Resume step verified", "status": "completed",
        "completed_steps": ["resume"], "pending_steps": [],
        "verification_job_id": "verification-job-001",
        "evidence": [{"kind": "test", "reference": "resume-test"}],
    })
    assert completed.status_code == 201, completed.text
    final_run = client.get(f"/v1/runs/{run['id']}", headers=owner).json()
    assert final_run["status"] == "completed"
    assert set(final_run["completed_steps"]) == {"schema", "resume"}

    hidden = client.get(f"/v1/projects/{project_id}", headers=other)
    assert hidden.status_code == 404
    hidden_run = client.get(f"/v1/runs/{run['id']}", headers=other)
    assert hidden_run.status_code == 404


def test_conversation_history_rename_archive_and_delete(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path / 'history.db'}")
    client = TestClient(app)
    headers = _workspace(client, "history")
    created = client.post("/v1/conversations", headers=headers, json={"title": "New engineering session"})
    assert created.status_code == 201, created.text
    conversation_id = created.json()["id"]

    renamed = client.patch(f"/v1/history/conversations/{conversation_id}", headers=headers, json={"title": "Release preparation"})
    assert renamed.status_code == 200
    assert renamed.json()["title"] == "Release preparation"
    assert client.get("/v1/history/conversations", headers=headers, params={"q": "release"}).json()[0]["id"] == conversation_id

    archived = client.post(f"/v1/history/conversations/{conversation_id}/archive", headers=headers)
    assert archived.status_code == 200
    assert client.get("/v1/history/conversations", headers=headers).json() == []
    assert client.get("/v1/history/conversations", headers=headers, params={"include_archived": "true"}).json()[0]["id"] == conversation_id

    deleted = client.delete(f"/v1/history/conversations/{conversation_id}", headers=headers)
    assert deleted.status_code == 204
    assert client.get(f"/v1/conversations/{conversation_id}", headers=headers).status_code == 404


def test_continuity_and_history_api_routes_are_registered():
    client = TestClient(app)
    paths = client.get("/openapi.json").json()["paths"]
    assert "/v1/projects" in paths
    assert "/v1/memory" in paths
    assert "/v1/runs/{run_id}/resume" in paths
    assert "/v1/runs/{run_id}/checkpoints" in paths
    assert "/v1/history/conversations" in paths
    assert "/v1/history/conversations/{conversation_id}/messages" in paths

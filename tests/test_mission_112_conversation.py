from fastapi.testclient import TestClient

from oae.api.app import app


def _client(tmp_path):
    import oae.api.auth as auth
    import oae.api.db as database

    db_path = tmp_path / "mission-112.db"
    database.settings.database_url = f"sqlite:///{db_path}"
    auth.settings.database_url = f"sqlite:///{db_path}"
    return TestClient(app)


def test_conversation_lifecycle_and_modes(tmp_path):
    client = _client(tmp_path)
    tenant = client.post("/v1/tenants", json={"name": "Mission 112"})
    assert tenant.status_code == 201
    headers = {"Authorization": f"Bearer {tenant.json()['api_key']}"}

    created = client.post(
        "/v1/conversations",
        headers=headers,
        json={"mode": "ask", "repository_id": "repo-1"},
    )
    assert created.status_code == 201
    conversation_id = created.json()["id"]

    message = client.post(
        f"/v1/conversations/{conversation_id}/messages",
        headers=headers,
        json={"content": "Fix the authentication bug and verify the repair.", "mode": "plan"},
    )
    assert message.status_code == 200
    body = message.json()
    assert body["mode"] == "plan"
    assert any(item["role"] == "user" for item in body["messages"])
    objective = [item for item in body["messages"] if item["role"] == "user"][-1]["metadata"]["objective"]
    assert objective["intent"] == "repair"
    assert objective["mode"] == "plan"

    updated = client.patch(
        f"/v1/conversations/{conversation_id}",
        headers=headers,
        json={"mode": "execute", "workspace_id": "workspace-1"},
    )
    assert updated.status_code == 200
    assert updated.json()["mode"] == "execute"
    assert updated.json()["workspace_id"] == "workspace-1"


def test_conversation_tenant_isolation(tmp_path):
    client = _client(tmp_path)
    first = client.post("/v1/tenants", json={"name": "First Tenant"})
    second = client.post("/v1/tenants", json={"name": "Second Tenant"})
    first_headers = {"Authorization": f"Bearer {first.json()['api_key']}"}
    second_headers = {"Authorization": f"Bearer {second.json()['api_key']}"}

    created = client.post("/v1/conversations", headers=first_headers, json={"title": "Private session"})
    assert created.status_code == 201
    conversation_id = created.json()["id"]

    assert client.get(f"/v1/conversations/{conversation_id}", headers=second_headers).status_code == 404


def test_multimodal_attachment_accepts_safe_types(tmp_path):
    client = _client(tmp_path)
    tenant = client.post("/v1/tenants", json={"name": "Attachment Tenant"})
    headers = {"Authorization": f"Bearer {tenant.json()['api_key']}"}
    created = client.post("/v1/conversations", headers=headers, json={})
    conversation_id = created.json()["id"]

    response = client.post(
        f"/v1/conversations/{conversation_id}/attachments",
        headers=headers,
        files={"file": ("spec.md", b"# Requirements", "text/markdown")},
    )
    assert response.status_code == 200
    attachment = [m for m in response.json()["messages"] if m["message_type"] == "attachment"][-1]
    assert attachment["metadata"]["filename"] == "spec.md"
    assert attachment["metadata"]["ingestion_status"] == "accepted"


def test_command_center_assets_are_referenced():
    client = TestClient(app)
    page = client.get("/")
    assert page.status_code == 200
    assert "/assets/command.css" in page.text
    assert "/assets/command.js" in page.text
    assert "What do you want me to build?" in client.get("/assets/command.js").text


def test_command_center_send_and_viewport_contract(tmp_path):
    client = _client(tmp_path)
    page = client.get("/")
    script = client.get("/assets/command.js")
    styles = client.get("/assets/command.css")
    assert page.status_code == 200
    assert script.status_code == 200
    assert styles.status_code == 200
    assert 'id="oae-send"' in script.text
    assert 'type="button"' in script.text
    assert 'addEventListener("click", send)' in script.text
    assert 'height:100dvh' in styles.text
    assert 'overflow:hidden' in styles.text
    assert 'min-height:0' in styles.text


def test_command_center_attachment_and_send_contract():
    client = TestClient(app)
    script = client.get("/assets/command.js").text
    styles = client.get("/assets/command.css").text
    assert "pendingFiles" in script
    assert "oae-pending-attachments" in script
    assert "ready to send" in script
    assert "allow attachment-only sends" not in script
    assert "if ((!content && !state.pendingFiles.length)" in script
    assert "new FormData()" in script
    assert ".oae-attachment-chip" in styles

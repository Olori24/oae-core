from fastapi.testclient import TestClient

from oae.api.app import app


def test_owner_can_issue_and_revoke_a_separate_approver_key(tmp_path):
    import oae.api.auth as auth
    import oae.api.db as database

    db_path = tmp_path / "principal-keys.db"
    database.settings.database_url = f"sqlite:///{db_path}"
    auth.settings.database_url = f"sqlite:///{db_path}"
    client = TestClient(app)
    tenant = client.post("/v1/tenants", json={"name": "Principal Owner"}).json()
    owner_headers = {"Authorization": f"Bearer {tenant['api_key']}"}

    issued = client.post(
        "/v1/principal-keys",
        headers=owner_headers,
        json={"principal_role": "approver", "principal_id": "approver-1"},
    )

    assert issued.status_code == 201
    issued_body = issued.json()
    assert issued_body["principal_role"] == "approver"
    assert issued_body["principal_id"] == "approver-1"
    approver_headers = {"Authorization": f"Bearer {issued_body['api_key']}"}
    assert client.get("/v1/me", headers=approver_headers).status_code == 200

    revoked = client.post(f"/v1/principal-keys/{issued_body['id']}/revoke", headers=owner_headers)
    assert revoked.status_code == 204
    assert client.get("/v1/me", headers=approver_headers).status_code == 401


def test_non_owner_cannot_issue_principal_keys(tmp_path):
    import oae.api.auth as auth
    import oae.api.db as database

    db_path = tmp_path / "principal-keys-non-owner.db"
    database.settings.database_url = f"sqlite:///{db_path}"
    auth.settings.database_url = f"sqlite:///{db_path}"
    client = TestClient(app)
    tenant = client.post("/v1/tenants", json={"name": "Non Owner"}).json()
    owner_headers = {"Authorization": f"Bearer {tenant['api_key']}"}
    operator = client.post(
        "/v1/principal-keys",
        headers=owner_headers,
        json={"principal_role": "operator", "principal_id": "operator-1"},
    ).json()

    response = client.post(
        "/v1/principal-keys",
        headers={"Authorization": f"Bearer {operator['api_key']}"},
        json={"principal_role": "approver", "principal_id": "approver-2"},
    )

    assert response.status_code == 403


def test_viewer_cannot_mutate_repositories_or_jobs(tmp_path):
    import oae.api.auth as auth
    import oae.api.db as database

    db_path = tmp_path / "viewer-mutations.db"
    database.settings.database_url = f"sqlite:///{db_path}"
    auth.settings.database_url = f"sqlite:///{db_path}"
    client = TestClient(app)

    tenant = client.post("/v1/tenants", json={"name": "Viewer Tenant"}).json()
    owner_headers = {"Authorization": f"Bearer {tenant['api_key']}"}
    issued = client.post(
        "/v1/principal-keys",
        headers=owner_headers,
        json={"principal_role": "viewer", "principal_id": "viewer-1"},
    )
    assert issued.status_code == 201
    viewer_headers = {"Authorization": f"Bearer {issued.json()['api_key']}"}

    repository = client.post(
        "/v1/repositories",
        headers=viewer_headers,
        json={
            "provider": "github",
            "external_id": "Olori24/oae-core",
            "clone_url": "https://github.com/Olori24/oae-core.git",
        },
    )
    assert repository.status_code == 403

    job = client.post(
        "/v1/jobs",
        headers=viewer_headers,
        json={"operation": "review", "payload": {"findings": []}},
    )
    assert job.status_code == 403


def test_build_is_fail_closed_when_governed_execution_is_disabled(tmp_path):
    import oae.api.auth as auth
    import oae.api.db as database
    from oae.api.config import settings

    db_path = tmp_path / "build-governance.db"
    database.settings.database_url = f"sqlite:///{db_path}"
    auth.settings.database_url = f"sqlite:///{db_path}"
    settings.database_url = f"sqlite:///{db_path}"
    settings.worker_authorization_enforcement_enabled = False
    client = TestClient(app)

    tenant = client.post("/v1/tenants", json={"name": "Build Tenant"}).json()
    response = client.post(
        "/v1/jobs",
        headers={"Authorization": f"Bearer {tenant['api_key']}"},
        json={
            "operation": "build",
            "payload": {"name": "demo", "description": "test"},
        },
    )
    assert response.status_code == 403

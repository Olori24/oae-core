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

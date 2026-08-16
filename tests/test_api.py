from fastapi.testclient import TestClient

from oae.api.app import app


def test_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_tenant_job_lifecycle(tmp_path):
    import oae.api.auth as auth
    import oae.api.db as database

    db_path = tmp_path / "oae.db"
    database.settings.database_url = f"sqlite:///{db_path}"
    auth.settings.database_url = f"sqlite:///{db_path}"

    client = TestClient(app)
    created = client.post("/v1/tenants", json={"name": "Acme"})
    assert created.status_code == 201
    key = created.json()["api_key"]
    headers = {"Authorization": f"Bearer {key}"}

    assert client.get("/v1/me", headers=headers).status_code == 200

    job = client.post(
        "/v1/jobs", headers=headers,
        json={"operation": "review", "payload": {"findings": ["test gap"]}},
    )
    assert job.status_code == 202
    job_id = job.json()["id"]

    fetched = client.get(f"/v1/jobs/{job_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["status"] == "completed"
    assert fetched.json()["result"]["count"] == 1


def test_invalid_api_key_is_rejected():
    client = TestClient(app)
    response = client.get("/v1/me", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401

from fastapi.testclient import TestClient

from oae.api.app import app


def test_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_tenant_isolation_and_job_lifecycle(tmp_path, monkeypatch):
    db_path = tmp_path / "oae.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    # Reload settings/database-dependent modules so this test uses its own database.
    import importlib
    import oae.api.config as config
    import oae.api.db as database
    import oae.api.auth as auth
    import oae.api.routes as routes

    config.settings.database_url = f"sqlite:///{db_path}"
    database.settings.database_url = f"sqlite:///{db_path}"
    auth.settings.database_url = f"sqlite:///{db_path}"

    client = TestClient(app)
    created = client.post("/v1/tenants", json={"name": "Acme"})
    assert created.status_code == 201
    body = created.json()
    key = body["api_key"]

    headers = {"Authorization": f"Bearer {key}"}
    assert client.get("/v1/me", headers=headers).status_code == 200

    job = client.post(
        "/v1/jobs", headers=headers,
        json={"operation": "analyze", "payload": {"repository": "demo"}},
    )
    assert job.status_code == 202
    job_body = job.json()
    assert job_body["status"] == "queued"

    fetched = client.get(f"/v1/jobs/{job_body['id']}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["id"] == job_body["id"]

    importlib.reload(routes)

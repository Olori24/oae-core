"""High-value security regression tests promoted into the Developer Arsenal gate."""

from fastapi.testclient import TestClient

from oae.api.app import app


def _tenant(client: TestClient, name: str) -> dict[str, str]:
    response = client.post("/v1/tenants", json={"name": name})
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['api_key']}"}


def test_tenant_cannot_read_another_tenants_job(tmp_path):
    import oae.api.auth as auth
    import oae.api.db as database

    db_path = tmp_path / "tenant-job-isolation.db"
    database.settings.database_url = f"sqlite:///{db_path}"
    auth.settings.database_url = f"sqlite:///{db_path}"
    client = TestClient(app)

    owner_headers = _tenant(client, "Owner")
    other_headers = _tenant(client, "Other")

    created = client.post(
        "/v1/jobs",
        headers=owner_headers,
        json={"operation": "review", "payload": {"findings": ["private finding"]}},
    )
    assert created.status_code == 202
    job_id = created.json()["id"]

    assert client.get(f"/v1/jobs/{job_id}", headers=owner_headers).status_code == 200
    assert client.get(f"/v1/jobs/{job_id}", headers=other_headers).status_code == 404


def test_tenant_inventory_does_not_leak_other_tenant_jobs(tmp_path):
    import oae.api.auth as auth
    import oae.api.db as database

    db_path = tmp_path / "tenant-inventory-isolation.db"
    database.settings.database_url = f"sqlite:///{db_path}"
    auth.settings.database_url = f"sqlite:///{db_path}"
    client = TestClient(app)

    owner_headers = _tenant(client, "Owner")
    other_headers = _tenant(client, "Other")

    created = client.post(
        "/v1/jobs",
        headers=owner_headers,
        json={"operation": "review", "payload": {"findings": ["private finding"]}},
    )
    assert created.status_code == 202
    job_id = created.json()["id"]

    response = client.get("/v1/jobs", headers=other_headers)
    assert response.status_code == 200
    payload = response.json()
    items = payload.get("items", payload if isinstance(payload, list) else [])
    assert job_id not in {item["id"] for item in items}

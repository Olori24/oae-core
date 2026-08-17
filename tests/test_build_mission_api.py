from fastapi.testclient import TestClient

from oae.api.app import app


def test_build_mission_is_exposed_as_real_saas_operation(tmp_path):
    import oae.api.auth as auth
    import oae.api.db as database

    db_path = tmp_path / "oae.db"
    database.settings.database_url = f"sqlite:///{db_path}"
    auth.settings.database_url = f"sqlite:///{db_path}"

    client = TestClient(app)
    created = client.post("/v1/tenants", json={"name": "TeamPulse Test"})
    assert created.status_code == 201
    headers = {"Authorization": f"Bearer {created.json()['api_key']}"}

    response = client.post(
        "/v1/jobs",
        headers=headers,
        json={
            "operation": "build",
            "payload": {
                "name": "TeamPulse",
                "description": "A developer workspace for engineering jobs and results.",
            },
        },
    )

    assert response.status_code == 202
    job_id = response.json()["id"]
    result = client.get(f"/v1/jobs/{job_id}", headers=headers)

    assert result.status_code == 200
    body = result.json()
    assert body["status"] == "completed"
    assert body["result"]["operation"] == "build"
    assert body["result"]["evidence"]["mission"]["application"] == "TeamPulse"
    assert body["result"]["evidence"]["mission"]["verified"] is True

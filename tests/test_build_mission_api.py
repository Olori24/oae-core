from fastapi.testclient import TestClient

from oae.api.app import app


def test_build_mission_requires_governed_worker_runtime(tmp_path):
    import oae.api.auth as auth
    import oae.api.db as database
    import oae.api.routes as routes

    db_path = tmp_path / "oae.db"
    database.settings.database_url = f"sqlite:///{db_path}"
    auth.settings.database_url = f"sqlite:///{db_path}"
    routes.settings.worker_authorization_enforcement_enabled = True
    database.settings.durable_jobs_enabled = False
    auth.settings.durable_jobs_enabled = False
    routes.settings.durable_jobs_enabled = False

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

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Build execution requires PostgreSQL durable jobs while authorization enforcement is enabled."
    )

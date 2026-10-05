from datetime import datetime, timezone

from fastapi.testclient import TestClient

from oae.api.app import app


def test_build_mission_is_exposed_as_real_saas_operation(tmp_path, monkeypatch):
    import oae.api.auth as auth
    import oae.api.db as database
    import oae.api.routes as routes

    db_path = tmp_path / "oae.db"
    database.settings.database_url = f"sqlite:///{db_path}"
    auth.settings.database_url = f"sqlite:///{db_path}"
    routes.settings.worker_authorization_enforcement_enabled = True
    routes.settings.database_backend = "postgres"
    routes.settings.durable_jobs_enabled = True
    database.settings.database_backend = "postgres"
    database.settings.durable_jobs_enabled = True
    auth.settings.database_backend = "postgres"
    auth.settings.durable_jobs_enabled = True

    class _DurableJob:
        id = "job-build-test"
        status = "queued"
        operation = "build"
        payload = {
            "name": "TeamPulse",
            "description": "A developer workspace for engineering jobs and results.",
        }
        created_at = datetime.now(timezone.utc)
        updated_at = created_at

    monkeypatch.setattr(
        routes.WorkerAuthorizationRepository,
        "is_approved_for_execution",
        lambda self, **_kwargs: True,
    )
    monkeypatch.setattr(
        routes.DurableJobRepository,
        "enqueue",
        lambda self, **_kwargs: _DurableJob(),
    )

    client = TestClient(app)
    created = client.post("/v1/tenants", json={"name": "TeamPulse Test"})
    assert created.status_code == 201
    headers = {"Authorization": f"Bearer {created.json()['api_key']}"}

    response = client.post(
        "/v1/jobs",
        headers=headers,
        json={
            "operation": "build",
            "authorization_id": "auth-build-test",
            "payload": {
                "name": "TeamPulse",
                "description": "A developer workspace for engineering jobs and results.",
            },
        },
    )

    assert response.status_code == 202
    body = response.json()
    assert body["id"] == "job-build-test"
    assert body["status"] == "queued"
    assert body["operation"] == "build"

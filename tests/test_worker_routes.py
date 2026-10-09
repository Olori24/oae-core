from fastapi.testclient import TestClient

from oae.api.app import app


def test_worker_tick_rejects_missing_cron_secret(monkeypatch):
    monkeypatch.setenv("CRON_SECRET", "expected")
    response = TestClient(app).post("/v1/worker/tick")
    assert response.status_code == 401

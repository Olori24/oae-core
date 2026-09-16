from fastapi.testclient import TestClient

from oae.api.app import app
from oae.api.observability import telemetry


def test_request_id_is_preserved_and_recorded():
    client = TestClient(app)
    request_id = "arsenal-wave2-request"

    response = client.get("/health", headers={"X-Request-ID": request_id})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id
    snapshot = telemetry.snapshot()
    assert snapshot["requests"].get("GET /health", 0) >= 1
    assert snapshot["requests"].get("status:200", 0) >= 1


def test_request_id_is_generated_when_missing():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    generated = response.headers.get("X-Request-ID")
    assert generated
    assert len(generated) == 36

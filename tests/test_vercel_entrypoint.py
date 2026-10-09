from fastapi.testclient import TestClient

from index import app


def test_vercel_entrypoint_serves_openapi_and_continuity_routes():
    client = TestClient(app)

    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    paths = response.json()["paths"]
    assert "/v1/projects" in paths
    assert "/v1/runs/{run_id}/resume" in paths
    assert "/v1/runs/{run_id}/checkpoints" in paths


def test_vercel_entrypoint_routes_api_requests_to_fastapi():
    response = TestClient(app).get("/v1/projects")

    # The request must reach FastAPI's authenticated API, not a static HTML fallback.
    assert response.status_code in {401, 403}
    assert "text/html" not in response.headers.get("content-type", "")

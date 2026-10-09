from fastapi.testclient import TestClient

from oae.api.app import app


def test_product_brief_requires_auth():
    response = TestClient(app).post(
        "/v1/product/brief",
        json={"idea": "Build a school management app for Nigerian schools."},
    )
    assert response.status_code == 401

def test_product_brief_is_tenant_scoped_and_deterministic_without_model(tmp_path):
    import oae.api.auth as auth
    import oae.api.db as database

    db_path = tmp_path / "product-builder.db"
    database.settings.database_url = f"sqlite:///{db_path}"
    auth.settings.database_url = f"sqlite:///{db_path}"
    client = TestClient(app)
    tenant = client.post("/v1/tenants", json={"name": "Builder"})
    headers = {"Authorization": f"Bearer {tenant.json()['api_key']}"}
    response = client.post(
        "/v1/product/brief",
        headers=headers,
        json={"idea": "Build a school management app where teachers take attendance and parents see results."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["brief"]["product_name"]
    assert "Teacher" in body["brief"]["entities"] or "Teacher" in body["brief"]["users"]
    assert body["ready"] is False

from fastapi.testclient import TestClient

from oae.api.app import app


def test_landing_page_is_available():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "Engineering command center" in response.text
    assert "Start a mission" in response.text
    assert "Missions" in response.text
    assert "Intelligence" in response.text
    assert "Security" in response.text
    assert "evidence-grid" in response.text


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

    review = client.post(
        "/v1/jobs",
        headers=headers,
        json={"operation": "review", "payload": {"findings": ["test gap"]}},
    )
    assert review.status_code == 202
    review_id = review.json()["id"]

    fetched = client.get(f"/v1/jobs/{review_id}", headers=headers)
    assert fetched.status_code == 200
    review_result = fetched.json()["result"]
    assert fetched.json()["status"] == "completed"
    assert review_result["count"] == 1
    assert review_result["schema_version"] == "1.0"
    assert review_result["evidence"]["finding_count"] == 1
    assert review_result["evidence"]["review_status"] == "recorded"

    verify = client.post(
        "/v1/jobs",
        headers=headers,
        json={"operation": "verify", "payload": {"success": True, "checks": ["control-plane"]}},
    )
    assert verify.status_code == 202
    verify_id = verify.json()["id"]

    verified = client.get(f"/v1/jobs/{verify_id}", headers=headers)
    assert verified.status_code == 200
    verify_result = verified.json()["result"]
    assert verify_result["verified"] is True
    assert verify_result["schema_version"] == "1.0"
    assert verify_result["evidence"]["verification_status"] == "passed"
    assert verify_result["evidence"]["check_count"] == 1


def test_tenant_can_register_repository_and_pin_revision(tmp_path):
    import oae.api.auth as auth
    import oae.api.db as database

    db_path = tmp_path / "repository-api.db"
    database.settings.database_url = f"sqlite:///{db_path}"
    auth.settings.database_url = f"sqlite:///{db_path}"
    client = TestClient(app)

    tenant = client.post("/v1/tenants", json={"name": "Repository Owner"})
    headers = {"Authorization": f"Bearer {tenant.json()['api_key']}"}
    repository = client.post(
        "/v1/repositories",
        headers=headers,
        json={
            "provider": "github",
            "external_id": "Olori24/oae-core",
            "clone_url": "https://github.com/Olori24/oae-core.git",
            "default_branch": "main",
            "credential_ref": "secret://oae/github-read-token",
        },
    )

    assert repository.status_code == 201
    repository_body = repository.json()
    assert repository_body["provider"] == "github"
    assert repository_body["external_id"] == "Olori24/oae-core"
    assert repository_body["status"] == "active"
    assert "credential_ref" not in repository_body

    commit_sha = "A" * 40
    revision = client.post(
        f"/v1/repositories/{repository_body['id']}/revisions",
        headers=headers,
        json={
            "commit_sha": commit_sha,
            "tree_sha": "b" * 40,
            "branch_name": "main",
            "manifest_sha256": "c" * 64,
        },
    )

    assert revision.status_code == 201
    assert revision.json()["repository_id"] == repository_body["id"]
    assert revision.json()["commit_sha"] == commit_sha.lower()
    assert revision.json()["manifest_sha256"] == "c" * 64
    assert client.post(
        f"/v1/repositories/{repository_body['id']}/revisions",
        headers=headers,
        json={"commit_sha": commit_sha.lower()},
    ).status_code == 409


def test_repository_registration_rejects_unsafe_and_duplicate_inputs(tmp_path):
    import oae.api.auth as auth
    import oae.api.db as database

    db_path = tmp_path / "repository-validation.db"
    database.settings.database_url = f"sqlite:///{db_path}"
    auth.settings.database_url = f"sqlite:///{db_path}"
    client = TestClient(app)

    tenant = client.post("/v1/tenants", json={"name": "Validation Owner"})
    headers = {"Authorization": f"Bearer {tenant.json()['api_key']}"}
    valid_payload = {
        "provider": "github",
        "external_id": "Olori24/oae-core",
        "clone_url": "https://github.com/Olori24/oae-core.git",
    }
    registered = client.post("/v1/repositories", headers=headers, json=valid_payload)
    assert registered.status_code == 201
    assert client.post("/v1/repositories", headers=headers, json=valid_payload).status_code == 409

    unsafe_clone = dict(valid_payload, clone_url="https://token@github.com/Olori24/oae-core.git")
    assert client.post("/v1/repositories", headers=headers, json=unsafe_clone).status_code == 422
    unsafe_secret = dict(valid_payload, credential_ref="github_pat_secret")
    assert client.post("/v1/repositories", headers=headers, json=unsafe_secret).status_code == 422
    unsafe_secret_query = dict(valid_payload, credential_ref="secret://oae/token?value=secret")
    assert client.post("/v1/repositories", headers=headers, json=unsafe_secret_query).status_code == 422
    assert client.post(
        f"/v1/repositories/{registered.json()['id']}/revisions",
        headers=headers,
        json={"commit_sha": "not-a-commit"},
    ).status_code == 422


def test_tenant_cannot_pin_revisions_for_another_tenant_repository(tmp_path):
    import oae.api.auth as auth
    import oae.api.db as database

    db_path = tmp_path / "repository-boundaries.db"
    database.settings.database_url = f"sqlite:///{db_path}"
    auth.settings.database_url = f"sqlite:///{db_path}"
    client = TestClient(app)

    owner = client.post("/v1/tenants", json={"name": "Repository Owner"})
    other = client.post("/v1/tenants", json={"name": "Other Tenant"})
    owner_headers = {"Authorization": f"Bearer {owner.json()['api_key']}"}
    other_headers = {"Authorization": f"Bearer {other.json()['api_key']}"}
    repository = client.post(
        "/v1/repositories",
        headers=owner_headers,
        json={
            "provider": "github",
            "external_id": "Olori24/oae-core",
            "clone_url": "https://github.com/Olori24/oae-core.git",
        },
    )

    response = client.post(
        f"/v1/repositories/{repository.json()['id']}/revisions",
        headers=other_headers,
        json={"commit_sha": "d" * 40},
    )
    assert response.status_code == 404


def test_invalid_api_key_is_rejected():
    client = TestClient(app)
    response = client.get("/v1/me", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401

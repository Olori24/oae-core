from fastapi.testclient import TestClient

from oae.api.app import app
from oae.api.github import GitHubPublicAnalyzer


def _sqlite_client(tmp_path):
    import oae.api.auth as auth
    import oae.api.db as database

    db_path = tmp_path / "beta-boundaries.db"
    database.settings.database_url = f"sqlite:///{db_path}"
    auth.settings.database_url = f"sqlite:///{db_path}"
    return TestClient(app)


def test_tenant_cannot_read_another_tenants_job(tmp_path):
    client = _sqlite_client(tmp_path)

    first = client.post("/v1/tenants", json={"name": "Developer One"})
    second = client.post("/v1/tenants", json={"name": "Developer Two"})
    first_key = first.json()["api_key"]
    second_key = second.json()["api_key"]

    job = client.post(
        "/v1/jobs",
        headers={"Authorization": f"Bearer {first_key}"},
        json={"operation": "review", "payload": {"findings": ["boundary"]}},
    )
    assert job.status_code == 202

    response = client.get(
        f"/v1/jobs/{job.json()['id']}",
        headers={"Authorization": f"Bearer {second_key}"},
    )
    assert response.status_code == 404


def test_public_analyzer_rejects_non_github_urls():
    analyzer = GitHubPublicAnalyzer()

    for url in (
        "http://github.com/owner/repo",
        "https://example.com/owner/repo",
        "https://github.com/owner",
        "https://github.com/owner/repo/issues/1",
        "https://github.com/owner/repo?redirect=https://example.com",
        "https://github.com/owner/repo#fragment",
    ):
        try:
            analyzer.analyze(url)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Expected ValueError for {url}")


def test_public_analyzer_refuses_non_github_api_fetch_before_network_access():
    analyzer = GitHubPublicAnalyzer()

    try:
        analyzer._get("https://example.com/metadata")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected the analyzer to reject a non-GitHub API URL")

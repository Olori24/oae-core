import json

from oae.core.frontend_build_verifier import FrontendBuildVerifier


def create_frontend(root):
    web = root / "web"
    web.mkdir(parents=True)
    (web / "package.json").write_text(
        json.dumps({
            "name": "oae-generated-web",
            "scripts": {"build": "next build"},
        }),
        encoding="utf-8",
    )
    return web


def test_missing_frontend_is_blocked(tmp_path):
    result = FrontendBuildVerifier().verify(tmp_path, execute_build=False)

    assert result["status"] == "blocked"
    assert result["passed"] is False


def test_build_contract_is_verified_without_execution(tmp_path):
    create_frontend(tmp_path)

    result = FrontendBuildVerifier().verify(tmp_path, execute_build=False)

    assert result["status"] == "ready"
    assert result["passed"] is True


def test_missing_build_script_is_blocked(tmp_path):
    web = create_frontend(tmp_path)
    (web / "package.json").write_text(
        json.dumps({"name": "demo", "scripts": {}}),
        encoding="utf-8",
    )

    result = FrontendBuildVerifier().verify(tmp_path, execute_build=False)

    assert result["status"] == "blocked"
    assert "build script" in result["detail"]

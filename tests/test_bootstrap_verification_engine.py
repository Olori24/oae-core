from oae.core.bootstrap_verification_engine import (
    BootstrapVerificationEngine,
)


def test_verify_success(tmp_path):
    (tmp_path / "README.md").write_text("")
    (tmp_path / "Dockerfile").write_text("")
    (tmp_path / "pyproject.toml").write_text("")
    (tmp_path / "requirements.txt").write_text("")
    (tmp_path / ".env.example").write_text("")
    (tmp_path / ".gitignore").write_text("")

    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / ".github" / "workflows" / "ci.yml").write_text("")

    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "scripts").mkdir()

    result = BootstrapVerificationEngine().verify(tmp_path)

    assert result["success"] is True


def test_verify_missing_files(tmp_path):
    result = BootstrapVerificationEngine().verify(tmp_path)

    assert result["success"] is False
    assert len(result["missing_files"]) > 0

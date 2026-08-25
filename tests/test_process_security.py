from pathlib import Path

import pytest

from oae.api.workspace_manager import GitRevisionMaterializer, PinnedRepositoryRevision
from oae.core.process_security import (
    ProcessPolicyError,
    run_allowed_test_command,
    run_git,
    validate_git_ref,
    validate_repository_url,
)
from oae.core.repository_scanner import RepositoryScanner
from oae.core.repository_test_runner import RepositoryTestRunner


@pytest.mark.parametrize("value", ["-c", "main..next", "main@{1}", "../branch", "branch/"])
def test_git_ref_validation_rejects_option_and_revision_expression_syntax(value):
    with pytest.raises(ProcessPolicyError):
        validate_git_ref(value)


@pytest.mark.parametrize(
    "url",
    [
        "file:///tmp/repository",
        "http://github.com/example/repository",
        "https://user:token@github.com/example/repository",
        "https://github.com/example/repository?ref=main",
        "https://github.com/example/../repository",
    ],
)
def test_repository_url_validation_rejects_non_private_clone_boundaries(url):
    with pytest.raises(ProcessPolicyError):
        validate_repository_url(url)


def test_git_runner_rejects_global_config_injection_before_process_execution():
    with pytest.raises(ProcessPolicyError):
        run_git(["-c", "core.sshCommand=unexpected", "status"])


def test_test_runner_allows_version_check_but_rejects_arbitrary_python_code():
    safe = run_allowed_test_command(["python", "--version"])
    rejected = RepositoryTestRunner().run(["python", "-c", "print('unsafe')"])

    assert safe.returncode == 0
    assert rejected["returncode"] == 126
    assert rejected["passed"] is False
    assert "arbitrary Python code" in rejected["stderr"]


def test_workspace_materializer_validates_clone_url_and_revision_before_git_execution(monkeypatch, tmp_path):
    import oae.api.workspace_manager as module

    calls = []

    def fake_run_git(arguments, **kwargs):
        calls.append((arguments, kwargs))
        if arguments[0] == "clone":
            Path(arguments[-1]).mkdir()

    monkeypatch.setattr(module, "run_git", fake_run_git)
    revision = PinnedRepositoryRevision(
        tenant_id="tenant-1",
        repository_id="repository-1",
        revision_id="revision-1",
        clone_url="https://github.com/example/repository.git",
        commit_sha="a" * 40,
    )

    GitRevisionMaterializer().materialize(revision, tmp_path / "checkout")

    assert [arguments[0] for arguments, _ in calls] == ["clone", "fetch", "checkout"]
    assert all(Path(kwargs["cwd"]).is_dir() for _, kwargs in calls)


def test_repository_scanner_skips_invalid_utf8_source_without_masking_other_errors(tmp_path):
    (tmp_path / "valid.py").write_text("value = 1\n", encoding="utf-8")
    (tmp_path / "invalid.py").write_bytes(b"\xff\xfe")

    scanned = RepositoryScanner().scan(tmp_path)

    assert scanned == {"valid.py": "value = 1\n"}

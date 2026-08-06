from oae.core.git_patch_application_engine import (
    GitPatchApplicationEngine,
)


def test_apply_patch():
    engine = GitPatchApplicationEngine()

    patch = {"status": "generated"}

    result = engine.apply(patch)

    assert result["status"] == "applied"
    assert result["branch"] == "oae/recovery-001"
    assert result["patch"] == patch


def test_apply_structure():
    engine = GitPatchApplicationEngine()

    result = engine.apply({})

    assert "status" in result
    assert "branch" in result
    assert "files_changed" in result

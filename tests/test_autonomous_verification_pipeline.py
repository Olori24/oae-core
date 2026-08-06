from oae.core.autonomous_verification_pipeline import (
    AutonomousVerificationPipeline,
)


def test_verify_patch():
    pipeline = AutonomousVerificationPipeline()

    patch = {
        "status": "generated",
        "patches": [],
    }

    result = pipeline.verify(patch)

    assert result["approved"] is True
    assert result["errors"] == []
    assert result["patch"] == patch


def test_verify_structure():
    pipeline = AutonomousVerificationPipeline()

    result = pipeline.verify({})

    assert "approved" in result
    assert "errors" in result
    assert "patch" in result


def test_empty_patch():
    pipeline = AutonomousVerificationPipeline()

    result = pipeline.verify({})

    assert result["approved"] is True

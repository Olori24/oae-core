from oae.core.engineering_verification_metrics import (
    EngineeringVerificationMetrics,
)


def test_collect():
    metrics = EngineeringVerificationMetrics()

    result = metrics.collect(
        tests_passed=10,
        tests_failed=2,
        files_changed=5,
    )

    assert result["tests_passed"] == 10
    assert result["tests_failed"] == 2
    assert result["files_changed"] == 5


def test_success_rate():
    metrics = EngineeringVerificationMetrics()

    result = metrics.collect(
        tests_passed=8,
        tests_failed=2,
        files_changed=1,
    )

    assert result["success_rate"] == 0.8


def test_zero_tests():
    metrics = EngineeringVerificationMetrics()

    result = metrics.collect(
        tests_passed=0,
        tests_failed=0,
        files_changed=0,
    )

    assert result["success_rate"] == 0.0

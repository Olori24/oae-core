import pytest

from oae.api.operation_policy import OperationClass, classify_operation


def test_supported_operations_have_explicit_safety_classes():
    assert classify_operation("analyze") == OperationClass.CONCURRENT_SAFE
    assert classify_operation("review") == OperationClass.CONCURRENT_SAFE
    assert classify_operation("verify") == OperationClass.CONCURRENT_SAFE
    assert classify_operation("build") == OperationClass.ISOLATED_WRITE


def test_unknown_operation_fails_closed():
    with pytest.raises(ValueError, match="no execution safety policy"):
        classify_operation("future_destructive_operation")

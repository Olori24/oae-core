"""Execution classification for autonomous engineering operations.

The worker uses this policy to prevent an operation from silently gaining
more concurrency than its safety model permits. Unknown operations fail
closed and require explicit policy registration.
"""

from enum import StrEnum


class OperationClass(StrEnum):
    READ_ONLY = "READ_ONLY"
    ISOLATED_WRITE = "ISOLATED_WRITE"
    CONCURRENT_SAFE = "CONCURRENT_SAFE"
    SERIALIZED = "SERIALIZED"
    HUMAN_APPROVAL_REQUIRED = "HUMAN_APPROVAL_REQUIRED"


OPERATION_CLASSES: dict[str, OperationClass] = {
    "analyze": OperationClass.CONCURRENT_SAFE,
    "review": OperationClass.CONCURRENT_SAFE,
    "verify": OperationClass.CONCURRENT_SAFE,
    # Build currently receives a unique mission workspace per job. It is not
    # classified as globally serialized, but it remains an isolated write.
    "build": OperationClass.ISOLATED_WRITE,
}


def classify_operation(operation: str) -> OperationClass:
    try:
        return OPERATION_CLASSES[operation]
    except KeyError as exc:
        raise ValueError(f"operation has no execution safety policy: {operation}") from exc

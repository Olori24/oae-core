from oae.core.decision_engine import Decision
from oae.core.secure_pipeline import SecureExecutionPipeline
from oae.security.request import ApprovalRequest


def test_high_confidence_action_is_auto_approved():
    pipeline = SecureExecutionPipeline()

    result = pipeline.evaluate(
        action="refactor",
        target="src/oae/runtime.py",
        confidence=0.95,
    )

    assert isinstance(result, Decision)
    assert result.requires_approval is False
    assert pipeline.ledger.count() == 2


def test_low_confidence_action_creates_request():
    pipeline = SecureExecutionPipeline()

    result = pipeline.evaluate(
        action="delete",
        target="src/oae/runtime.py",
        confidence=0.50,
    )

    assert isinstance(result, ApprovalRequest)
    assert result.status == "PENDING"
    assert pipeline.ledger.count() == 2
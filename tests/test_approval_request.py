from oae.security.request import ApprovalRequest


def test_new_request_is_pending():
    request = ApprovalRequest(
        action="delete",
        target="src/oae/runtime.py",
        reason="Obsolete module",
        requester="Planner",
    )

    assert request.status == "PENDING"


def test_request_can_be_approved():
    request = ApprovalRequest(
        action="delete",
        target="src/oae/runtime.py",
        reason="Obsolete module",
        requester="Planner",
    )

    request.approve()

    assert request.status == "APPROVED"


def test_request_can_be_rejected():
    request = ApprovalRequest(
        action="delete",
        target="src/oae/runtime.py",
        reason="Obsolete module",
        requester="Planner",
    )

    request.reject()

    assert request.status == "REJECTED"
from oae.core.human_approval_gateway import (
    HumanApprovalGateway,
)


def test_request():
    gateway = HumanApprovalGateway()

    result = gateway.request({})

    assert result["approved"] is False
    assert result["status"] == "pending"


def test_structure():
    gateway = HumanApprovalGateway()

    result = gateway.request({})

    assert "approved" in result
    assert "status" in result
    assert "patch" in result

from oae.security.kernel import SecurityKernel


def test_read_repository_allowed():
    security = SecurityKernel()

    assert security.authorize("read_repository") is True


def test_write_requires_permission_and_approval():
    security = SecurityKernel()

    # Denied by permissions
    assert security.authorize("write_repository") is False

    # Grant permission
    security.permissions.allow("write_repository")

    # Still denied (approval required)
    assert security.authorize("write_repository") is False

    # Human approves
    security.approvals.approve("write_repository")

    # Now allowed
    assert security.authorize("write_repository") is True

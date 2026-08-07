from oae.capabilities.capability_resolver import (
    CapabilityResolver,
)


def test_resolve_kubernetes():

    resolver = CapabilityResolver()

    result = resolver.resolve(
        "Kubernetes",
    )

    assert result == [
        "Docker",
        "Docker Compose",
        "Container Deployment",
        "Kubernetes",
    ]


def test_resolve_rbac():

    resolver = CapabilityResolver()

    result = resolver.resolve(
        "RBAC",
    )

    assert result == [
        "Authentication",
        "Authorization",
        "RBAC",
    ]

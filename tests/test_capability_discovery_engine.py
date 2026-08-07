from oae.capabilities.capability_discovery_engine import (
    CapabilityDiscoveryEngine,
)


def test_discover(tmp_path):

    engine = CapabilityDiscoveryEngine()

    capabilities = engine.discover(tmp_path)

    names = {
        capability.name
        for capability in capabilities
    }

    assert "Docker" in names
    assert "CI/CD" in names
    assert "Testing" in names
    assert "Documentation" in names

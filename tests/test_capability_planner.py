from oae.capabilities.capability import Capability

from oae.capabilities.capability_planner import (
    CapabilityPlanner,
)


def test_planner():

    planner = CapabilityPlanner()

    capabilities = [
        Capability(
            "Docker",
            "Missing Docker",
            1,
        ),
    ]

    semantic = [
        (
            "Logging",
            "Logging missing",
            1,
        ),
    ]

    missions = planner.plan(
        capabilities,
        semantic,
    )

    titles = {
        mission.title
        for mission in missions
    }

    assert "Implement Docker" in titles

    assert "Implement Logging" in titles

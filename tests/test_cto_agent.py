from oae.agents.cto_agent import CTOAgent
from oae.capabilities.capability_planner import CapabilityMission


def test_cto_assignments():

    missions = [
        CapabilityMission(
            title="Implement Logging",
            priority=1,
            description="",
        ),
        CapabilityMission(
            title="Implement Middleware",
            priority=2,
            description="",
        ),
    ]

    tasks = CTOAgent().assign(missions)

    assert len(tasks) == 2

    assert tasks[0].owner == "Backend Engineer"

    assert tasks[1].owner == "Backend Engineer"

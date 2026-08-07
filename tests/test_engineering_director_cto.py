from oae.core.engineering_director import EngineeringDirector
from oae.capabilities.capability_planner import CapabilityMission


def test_engineering_director_review():

    director = EngineeringDirector()

    missions = [
        CapabilityMission(
            title="Implement Logging",
            priority=1,
            description="",
        )
    ]

    assignments = director.review(missions)

    assert len(assignments) == 1

    assert assignments[0].owner == "Backend Engineer"

    assert assignments[0].title == "Implement Logging"

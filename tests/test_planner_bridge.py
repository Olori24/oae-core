from oae.meta.planner_bridge import PlannerBridge


def test_create_specification():

    bridge = PlannerBridge()

    spec = bridge.create_specification(
        "Cache"
    )

    assert spec.name == "CacheGenerator"

    assert "Cache" in spec.description

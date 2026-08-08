from oae.core.engineering_director import EngineeringDirector


def test_creation():
    director = EngineeringDirector()

    assert director is not None


def test_register_engineer():
    director = EngineeringDirector()

    director.register("Backend Engineer")

    result = director.assign("Authentication")

    assert result["engineer"] == "Backend Engineer"


def test_assignment_contains_mission():
    director = EngineeringDirector()

    director.register("Backend Engineer")

    result = director.assign("JWT")

    assert result["mission"] == "JWT"


def test_no_engineers():
    director = EngineeringDirector()

    assert director.assign("JWT") is None


def test_multiple_engineers():
    director = EngineeringDirector()

    director.register("Backend Engineer")
    director.register("QA Engineer")

    result = director.assign("API")

    assert result["engineer"] in [
        "Backend Engineer",
        "QA Engineer",
    ]

def test_experience_returns_memory_report():
    from oae.core.engineering_director import EngineeringDirector

    director = EngineeringDirector()

    director.ledger.record(
        "MISSION_FAILED",
        "Authentication deployment failed",
    )

    director.ledger.record(
        "MISSION_COMPLETED",
        "Authentication deployment verified",
    )

    report = director.experience("authentication")

    assert report["match_count"] == 2
    assert report["completed"] == 1
    assert report["failed"] == 1
    assert report["success_rate"] == 0.5


def test_recommendation_returns_advisory_result():
    from oae.core.engineering_director import EngineeringDirector

    director = EngineeringDirector()

    director.ledger.record(
        "MISSION_FAILED",
        "Authentication deployment failed",
    )

    director.ledger.record(
        "MISSION_COMPLETED",
        "Authentication deployment verified",
    )

    result = director.recommend("authentication")

    assert result["recommendation"] == "review_historical_failures"
    assert result["confidence"] == 0.5

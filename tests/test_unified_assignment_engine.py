from oae.core.unified_assignment_engine import UnifiedAssignmentEngine


def test_creation():
    engine = UnifiedAssignmentEngine()

    assert engine is not None


def test_register():
    engine = UnifiedAssignmentEngine()

    engine.register("Backend Engineer")

    result = engine.assign("Backend API")

    assert result["engineer"] == "Backend Engineer"


def test_assignment_contains_mission():
    engine = UnifiedAssignmentEngine()

    engine.register("Backend Engineer")

    result = engine.assign("Authentication")

    assert result["mission"] == "Authentication"


def test_no_engineers():
    engine = UnifiedAssignmentEngine()

    assert engine.assign("Authentication") is None


def test_multiple_engineers():
    engine = UnifiedAssignmentEngine()

    engine.register("Backend Engineer")
    engine.register("QA Engineer")

    result = engine.assign("Backend API")

    assert result["engineer"] in [
        "Backend Engineer",
        "QA Engineer",
    ]
from oae.core.autonomous_execution_pipeline import AutonomousExecutionPipeline


def test_creation():
    pipeline = AutonomousExecutionPipeline()

    assert pipeline is not None


def test_register_engineer():
    pipeline = AutonomousExecutionPipeline()

    pipeline.register("Backend Engineer")

    result = pipeline.execute("Backend API")

    assert result["engineer"] == "Backend Engineer"


def test_mission_preserved():
    pipeline = AutonomousExecutionPipeline()

    pipeline.register("Backend Engineer")

    result = pipeline.execute("Authentication")

    assert result["mission"] == "Authentication"


def test_no_engineers():
    pipeline = AutonomousExecutionPipeline()

    assert pipeline.execute("Authentication") is None


def test_multiple_engineers():
    pipeline = AutonomousExecutionPipeline()

    pipeline.register("Backend Engineer")
    pipeline.register("QA Engineer")

    result = pipeline.execute("JWT")

    assert result["engineer"] in [
        "Backend Engineer",
        "QA Engineer",
    ]
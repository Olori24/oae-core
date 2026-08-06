from oae.core.autonomous_engineering_pipeline import (
    AutonomousEngineeringPipeline,
)


def test_creation():
    pipeline = AutonomousEngineeringPipeline()

    assert pipeline is not None


def test_empty_repository():
    pipeline = AutonomousEngineeringPipeline()

    result = pipeline.execute([])

    assert result == []


def test_single_file():
    pipeline = AutonomousEngineeringPipeline()

    pipeline.register("Backend Engineer")

    result = pipeline.execute(["auth.py"])

    assert len(result) == 1


def test_multiple_files():
    pipeline = AutonomousEngineeringPipeline()

    pipeline.register("Backend Engineer")

    result = pipeline.execute(
        [
            "auth.py",
            "models.py",
            "tests.py",
        ]
    )

    assert len(result) == 3


def test_contains_engineer():
    pipeline = AutonomousEngineeringPipeline()

    pipeline.register("Backend Engineer")

    result = pipeline.execute(["auth.py"])

    assert result[0]["engineer"] == "Backend Engineer"
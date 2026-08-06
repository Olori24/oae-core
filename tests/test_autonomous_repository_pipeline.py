from oae.core.autonomous_repository_pipeline import (
    AutonomousRepositoryPipeline,
)


def test_creation():
    pipeline = AutonomousRepositoryPipeline()

    assert pipeline is not None


def test_empty_repository():
    pipeline = AutonomousRepositoryPipeline()

    assert pipeline.process([]) == []


def test_single_file():
    pipeline = AutonomousRepositoryPipeline()

    missions = pipeline.process(["auth.py"])

    assert len(missions) == 1


def test_generated_title():
    pipeline = AutonomousRepositoryPipeline()

    missions = pipeline.process(["auth.py"])

    assert missions[0]["title"] == "Resolve Review auth.py"


def test_contains_agent():
    pipeline = AutonomousRepositoryPipeline()

    missions = pipeline.process(["auth.py"])

    assert "recommended_agent" in missions[0]
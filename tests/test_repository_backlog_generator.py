from oae.core.repository_backlog_generator import (
    RepositoryBacklogGenerator,
)


def test_creation():
    generator = RepositoryBacklogGenerator()

    assert generator is not None


def test_low_priority():
    generator = RepositoryBacklogGenerator()

    diagnosis = {
        "health": 100,
        "functions": 10,
        "classes": 5,
    }

    backlog = generator.generate(diagnosis)

    assert backlog[0]["priority"] == "LOW"


def test_health_issue():
    generator = RepositoryBacklogGenerator()

    diagnosis = {
        "health": 80,
        "functions": 20,
        "classes": 5,
    }

    backlog = generator.generate(diagnosis)

    assert any(
        item["title"] == "Improve repository health"
        for item in backlog
    )


def test_large_repository():
    generator = RepositoryBacklogGenerator()

    diagnosis = {
        "health": 85,
        "functions": 700,
        "classes": 20,
    }

    backlog = generator.generate(diagnosis)

    assert any(
        item["title"] == "Refactor oversized codebase"
        for item in backlog
    )


def test_architecture_review():
    generator = RepositoryBacklogGenerator()

    diagnosis = {
        "health": 95,
        "functions": 100,
        "classes": 150,
    }

    backlog = generator.generate(diagnosis)

    assert any(
        item["title"] == "Review architecture"
        for item in backlog
    )

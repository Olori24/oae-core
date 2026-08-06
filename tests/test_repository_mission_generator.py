from oae.core.repository_mission_generator import (
    RepositoryMissionGenerator,
)


def test_creation():
    generator = RepositoryMissionGenerator()

    assert generator is not None


def test_empty_findings():
    generator = RepositoryMissionGenerator()

    missions = generator.generate([])

    assert missions == []


def test_single_finding():
    generator = RepositoryMissionGenerator()

    missions = generator.generate(
        ["Unused import in auth.py"]
    )

    assert len(missions) == 1
    assert missions[0]["title"] == "Unused import in auth.py"


def test_multiple_findings():
    generator = RepositoryMissionGenerator()

    findings = [
        "Unused import",
        "Missing tests",
        "Security issue",
    ]

    missions = generator.generate(findings)

    assert len(missions) == 3


def test_default_priority():
    generator = RepositoryMissionGenerator()

    missions = generator.generate(["Dead code"])

    assert missions[0]["priority"] == 5
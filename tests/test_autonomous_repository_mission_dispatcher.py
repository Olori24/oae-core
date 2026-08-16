from oae.core.autonomous_repository_mission_dispatcher import (
    AutonomousRepositoryMissionDispatcher,
)


def test_dispatch():
    dispatcher = AutonomousRepositoryMissionDispatcher()

    dispatcher.dispatch(
        "opportunity-radar-africa",
        "Build authentication",
    )

    assert len(
        dispatcher.missions(
            "opportunity-radar-africa"
        )
    ) == 1


def test_multiple_repositories():
    dispatcher = AutonomousRepositoryMissionDispatcher()

    dispatcher.dispatch("repo1", "Mission A")
    dispatcher.dispatch("repo2", "Mission B")

    repos = dispatcher.repositories()

    assert "repo1" in repos
    assert "repo2" in repos


def test_clear():
    dispatcher = AutonomousRepositoryMissionDispatcher()

    dispatcher.dispatch("repo", "Mission")

    dispatcher.clear("repo")

    assert dispatcher.missions("repo") == []

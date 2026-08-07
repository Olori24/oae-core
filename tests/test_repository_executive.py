from oae.core.repository_executive import RepositoryExecutive


def test_register():
    executive = RepositoryExecutive()

    executive.register("repo")

    assert "repo" in executive.repositories()


def test_add_mission():
    executive = RepositoryExecutive()

    executive.add_mission("repo", "Mission")

    assert executive.mission_count("repo") == 1


def test_next_repository():
    executive = RepositoryExecutive()

    executive.add_mission("repo1", "A")
    executive.add_mission("repo1", "B")
    executive.add_mission("repo2", "C")

    assert executive.next_repository() == "repo1"


def test_empty():
    executive = RepositoryExecutive()

    assert executive.next_repository() is None

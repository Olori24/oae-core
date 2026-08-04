from oae.repository.service import RepositoryService


def test_repository_service():

    repo = RepositoryService()

    snapshot = repo.create_snapshot("repository")

    assert snapshot == "snapshot-1"

    assert repo.restore_snapshot(snapshot) == "repository"

    assert len(repo.list_snapshots()) == 1

    assert repo.delete_snapshot(snapshot) is True

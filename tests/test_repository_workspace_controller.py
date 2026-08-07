from oae.core.repository_workspace_controller import (
    RepositoryWorkspaceController,
)


def test_create_workspace(tmp_path):
    controller = RepositoryWorkspaceController(tmp_path)

    repo = controller.create("opportunity-radar-africa")

    assert repo.exists()
    assert controller.exists("opportunity-radar-africa")


def test_list_repositories(tmp_path):
    controller = RepositoryWorkspaceController(tmp_path)

    controller.create("repo1")
    controller.create("repo2")

    repos = controller.list_repositories()

    assert "repo1" in repos
    assert "repo2" in repos

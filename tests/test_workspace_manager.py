from oae.core.workspace_manager import WorkspaceManager


def test_workspace_creation(tmp_path):
    manager = WorkspaceManager(tmp_path)

    workspace = manager.create_workspace(
        "opportunity-radar-africa"
    )

    assert workspace.exists()

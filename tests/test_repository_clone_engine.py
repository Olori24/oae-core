from oae.core.repository_clone_engine import RepositoryCloneEngine


def test_workspace_created(tmp_path):
    engine = RepositoryCloneEngine(tmp_path)

    assert engine.workspace.exists()

from oae.core.repository_sandbox import RepositorySandbox


def test_sandbox_creation():
    sandbox = RepositorySandbox()

    path = sandbox.workspace_path()

    assert path.exists()
    assert path.is_dir()

    sandbox.cleanup()

    assert not path.exists()
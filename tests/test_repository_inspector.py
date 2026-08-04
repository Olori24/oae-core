from oae.repository import RepositoryInspector


def test_repository_inspector():

    inspector = RepositoryInspector()

    profile = inspector.inspect(".")

    assert profile.has_pyproject is True
    assert profile.uses_pytest is True

    assert profile.language == "Python"
    assert profile.package_manager == "pip"

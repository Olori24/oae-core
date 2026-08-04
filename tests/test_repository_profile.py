from oae.repository.profile import RepositoryProfile


def test_repository_profile_summary():

    profile = RepositoryProfile()

    profile.language = "Python"
    profile.package_manager = "pip"
    profile.has_git = True

    summary = profile.summary()

    assert summary["language"] == "Python"
    assert summary["package_manager"] == "pip"
    assert summary["git"] is True

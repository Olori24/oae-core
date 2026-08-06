from oae.core.github_actions_generator import GitHubActionsGenerator


def test_generate(tmp_path):
    path = GitHubActionsGenerator().generate(tmp_path)

    assert path.exists()

from oae.core.repository_test_runner import RepositoryTestRunner


def test_runner_returns_structure():
    runner = RepositoryTestRunner()

    result = runner.run()

    assert "returncode" in result
    assert "passed" in result
    assert "stdout" in result
    assert "stderr" in result


def test_passed_is_boolean():
    runner = RepositoryTestRunner()

    result = runner.run()

    assert isinstance(result["passed"], bool)


def test_returncode_is_integer():
    runner = RepositoryTestRunner()

    result = runner.run()

    assert isinstance(result["returncode"], int)

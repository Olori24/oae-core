from oae.core.git_checkout_engine import GitCheckoutEngine


def test_checkout_invalid_branch():
    engine = GitCheckoutEngine()

    result = engine.checkout("branch_that_should_not_exist")

    assert "returncode" in result
    assert "stdout" in result
    assert "stderr" in result
    assert result["branch"] == "branch_that_should_not_exist"


def test_create_branch_structure():
    engine = GitCheckoutEngine()

    result = engine.create_and_checkout("oae-test")

    assert "returncode" in result
    assert "stdout" in result
    assert "stderr" in result
    assert result["branch"] == "oae-test"

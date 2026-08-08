from oae.core.failure_classifier import FailureClassifier


def test_import_error():

    classifier = FailureClassifier()

    result = classifier.classify(
        {
            "passed": False,
            "returncode": 1,
            "stdout": "",
            "stderr": "ImportError: cannot import name Foo",
        }
    )

    assert result == "IMPORT_ERROR"


def test_syntax_error():

    classifier = FailureClassifier()

    result = classifier.classify(
        {
            "passed": False,
            "returncode": 1,
            "stdout": "",
            "stderr": "SyntaxError: invalid syntax",
        }
    )

    assert result == "SYNTAX_ERROR"


def test_test_failure():

    classifier = FailureClassifier()

    result = classifier.classify(
        {
            "passed": False,
            "returncode": 1,
            "stdout": "",
            "stderr": "AssertionError: expected 1 got 2",
        }
    )

    assert result == "TEST_FAILURE"


def test_runtime_error():

    classifier = FailureClassifier()

    result = classifier.classify(
        {
            "passed": False,
            "returncode": 1,
            "stdout": "",
            "stderr": "Traceback (most recent call last):\nRuntimeError: failed",
        }
    )

    assert result == "RUNTIME_ERROR"


def test_command_error():

    classifier = FailureClassifier()

    result = classifier.classify(
        {
            "passed": False,
            "returncode": 127,
            "stdout": "",
            "stderr": "",
        }
    )

    assert result == "COMMAND_ERROR"


def test_unknown_failure():

    classifier = FailureClassifier()

    result = classifier.classify(
        {
            "passed": False,
            "returncode": 1,
            "stdout": "",
            "stderr": "",
        }
    )

    assert result == "COMMAND_ERROR"


def test_success_has_no_failure():

    classifier = FailureClassifier()

    result = classifier.classify(
        {
            "passed": True,
            "returncode": 0,
            "stdout": "551 passed",
            "stderr": "",
        }
    )

    assert result == "NO_FAILURE"

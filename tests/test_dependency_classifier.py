from oae.core.dependency_classifier import DependencyClassifier


def test_web_dependency():
    classifier = DependencyClassifier()

    result = classifier.classify("fastapi")

    assert result.category == "Web"


def test_database_dependency():
    classifier = DependencyClassifier()

    result = classifier.classify("sqlalchemy")

    assert result.category == "Database"


def test_testing_dependency():
    classifier = DependencyClassifier()

    result = classifier.classify("pytest")

    assert result.category == "Testing"


def test_ai_dependency():
    classifier = DependencyClassifier()

    result = classifier.classify("openai")

    assert result.category == "AI"


def test_unknown_dependency():
    classifier = DependencyClassifier()

    result = classifier.classify("my_custom_library")

    assert result.category == "Other"
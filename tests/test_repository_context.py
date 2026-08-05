from oae.core.repository_context import RepositoryContextEngine


def test_repository_context_detects_python():
    engine = RepositoryContextEngine()

    context = engine.analyze()

    assert context.language == "Python"


def test_repository_has_tests():
    engine = RepositoryContextEngine()

    context = engine.analyze()

    assert context.has_tests is True


def test_repository_has_readme():
    engine = RepositoryContextEngine()

    context = engine.analyze()

    assert context.has_readme is True


def test_repository_has_git():
    engine = RepositoryContextEngine()

    context = engine.analyze()

    assert context.has_git is True
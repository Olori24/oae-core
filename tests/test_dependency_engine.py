from oae.core.dependency_engine import DependencyEngine


def test_dependency_engine_creation():
    engine = DependencyEngine()

    assert engine is not None


def test_dependency_report():
    engine = DependencyEngine()

    report = engine.analyze()

    assert isinstance(report.dependencies, list)


def test_requirements_are_strings():
    engine = DependencyEngine()

    report = engine.analyze()

    for dependency in report.dependencies:
        assert isinstance(dependency, str)
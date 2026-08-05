from oae.core.dependency_engine import DependencyEngine
from oae.core.dependency_classifier import ClassifiedDependency


def test_dependency_engine_creation():
    engine = DependencyEngine()

    assert engine is not None


def test_dependency_report():
    engine = DependencyEngine()

    report = engine.analyze()

    assert isinstance(report.dependencies, list)


def test_dependencies_are_classified():
    engine = DependencyEngine()

    report = engine.analyze()

    for dependency in report.dependencies:
        assert isinstance(dependency, ClassifiedDependency)


def test_dependency_has_category():
    engine = DependencyEngine()

    report = engine.analyze()

    for dependency in report.dependencies:
        assert isinstance(dependency.category, str)
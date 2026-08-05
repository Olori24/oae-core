from oae.core.impact_analyzer import ImpactAnalyzer
from oae.core.knowledge_graph import KnowledgeGraph


def test_no_impact():
    graph = KnowledgeGraph()

    analyzer = ImpactAnalyzer(graph)

    report = analyzer.analyze("planner")

    assert report.target == "planner"
    assert report.affected == []


def test_single_dependency():
    graph = KnowledgeGraph()

    graph.connect("planner", "executor")

    analyzer = ImpactAnalyzer(graph)

    report = analyzer.analyze("planner")

    assert report.affected == ["executor"]


def test_multiple_dependencies():
    graph = KnowledgeGraph()

    graph.connect("planner", "executor")
    graph.connect("planner", "mission_runner")

    analyzer = ImpactAnalyzer(graph)

    report = analyzer.analyze("planner")

    assert len(report.affected) == 2
    assert "executor" in report.affected
    assert "mission_runner" in report.affected


def test_unknown_target():
    graph = KnowledgeGraph()

    analyzer = ImpactAnalyzer(graph)

    report = analyzer.analyze("unknown")

    assert report.affected == []
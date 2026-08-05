from oae.core.knowledge_graph import KnowledgeGraph


def test_add_node():
    graph = KnowledgeGraph()

    graph.add_node("planner")

    assert "planner" in graph.nodes


def test_connect_nodes():
    graph = KnowledgeGraph()

    graph.connect("planner", "executor")

    assert "executor" in graph.neighbors("planner")


def test_duplicate_connection():
    graph = KnowledgeGraph()

    graph.connect("planner", "executor")
    graph.connect("planner", "executor")

    assert len(graph.neighbors("planner")) == 1


def test_unknown_node():
    graph = KnowledgeGraph()

    assert graph.neighbors("missing") == []
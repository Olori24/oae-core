from oae.core.call_graph_builder import CallGraphBuilder

SOURCE = """
def login():
    authenticate()
    log()

def authenticate():
    validate()

def validate():
    pass

def log():
    pass
"""


def test_creation():
    builder = CallGraphBuilder()

    assert builder is not None


def test_graph():
    builder = CallGraphBuilder()

    graph = builder.build(SOURCE)

    assert "login" in graph
    assert "authenticate" in graph["login"]
    assert "log" in graph["login"]


def test_nested():
    builder = CallGraphBuilder()

    graph = builder.build(SOURCE)

    assert "validate" in graph["authenticate"]


def test_leaf():
    builder = CallGraphBuilder()

    graph = builder.build(SOURCE)

    assert graph["validate"] == []
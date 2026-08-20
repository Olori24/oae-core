from oae.core.repository_knowledge_graph import (
    RepositoryKnowledgeGraph,
)

FILES = {
    "auth.py": """
import os

class Auth:
    pass

def login():
    pass
""",
    "models.py": """
class User:
    pass

def save():
    pass
""",
}


def test_creation():
    graph = RepositoryKnowledgeGraph()

    assert graph is not None


def test_build():
    graph = RepositoryKnowledgeGraph()

    result = graph.build(FILES)

    assert len(result) == 2


def test_auth_functions():
    graph = RepositoryKnowledgeGraph()

    result = graph.build(FILES)

    assert "login" in result["auth.py"]["functions"]


def test_auth_classes():
    graph = RepositoryKnowledgeGraph()

    result = graph.build(FILES)

    assert "Auth" in result["auth.py"]["classes"]


def test_models_classes():
    graph = RepositoryKnowledgeGraph()

    result = graph.build(FILES)

    assert "User" in result["models.py"]["classes"]


def test_imports():
    graph = RepositoryKnowledgeGraph()

    result = graph.build(FILES)

    assert "os" in result["auth.py"]["imports"]
from oae.core.python_ast_parser import PythonASTParser


SAMPLE = """
import os
from pathlib import Path

class User:
    pass

def login():
    pass

def logout():
    pass
"""


def test_creation():
    parser = PythonASTParser()

    assert parser is not None


def test_parse():
    parser = PythonASTParser()

    tree = parser.parse(SAMPLE)

    assert tree is not None


def test_functions():
    parser = PythonASTParser()

    tree = parser.parse(SAMPLE)

    assert parser.functions(tree) == [
        "login",
        "logout",
    ]


def test_classes():
    parser = PythonASTParser()

    tree = parser.parse(SAMPLE)

    assert parser.classes(tree) == [
        "User",
    ]


def test_imports():
    parser = PythonASTParser()

    tree = parser.parse(SAMPLE)

    imports = parser.imports(tree)

    assert "os" in imports
    assert "pathlib" in imports
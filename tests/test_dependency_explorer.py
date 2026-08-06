from oae.core.dependency_explorer import DependencyExplorer

GRAPH = {
    "auth.py": {
        "imports": ["os", "models"],
        "functions": ["login"],
        "classes": ["Auth"],
    },
    "models.py": {
        "imports": [],
        "functions": ["save"],
        "classes": ["User"],
    },
}


def test_creation():
    explorer = DependencyExplorer()
    assert explorer is not None


def test_imports():
    explorer = DependencyExplorer()
    assert "os" in explorer.imports_of(GRAPH, "auth.py")


def test_files_importing():
    explorer = DependencyExplorer()
    assert "auth.py" in explorer.files_importing(GRAPH, "models")


def test_functions():
    explorer = DependencyExplorer()
    assert "login" in explorer.functions(GRAPH)
    assert "save" in explorer.functions(GRAPH)


def test_classes():
    explorer = DependencyExplorer()
    assert "Auth" in explorer.classes(GRAPH)
    assert "User" in explorer.classes(GRAPH)
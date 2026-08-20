from oae.core.symbol_resolver import SymbolResolver

GRAPH = {
    "auth.py": {
        "functions": ["login", "logout"],
        "classes": ["Auth"],
    },
    "models.py": {
        "functions": ["save"],
        "classes": ["User"],
    },
}


def test_creation():
    resolver = SymbolResolver()

    assert resolver is not None


def test_function_resolution():
    resolver = SymbolResolver()

    assert resolver.resolve_function(
        GRAPH,
        "login",
    ) == "auth.py"


def test_class_resolution():
    resolver = SymbolResolver()

    assert resolver.resolve_class(
        GRAPH,
        "User",
    ) == "models.py"


def test_missing_symbol():
    resolver = SymbolResolver()

    assert resolver.resolve_function(
        GRAPH,
        "missing",
    ) is None


def test_symbol_index():
    resolver = SymbolResolver()

    symbols = resolver.symbols(GRAPH)

    assert symbols["login"] == "auth.py"
    assert symbols["User"] == "models.py"
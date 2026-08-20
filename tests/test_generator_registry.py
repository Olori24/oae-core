
from oae.meta.generator_registry import GeneratorRegistry


def test_generator_registry(tmp_path):

    core = (
        tmp_path
        / "src"
        / "oae"
        / "core"
    )

    core.mkdir(parents=True)

    (core / "cache_generator.py").write_text("")

    (core / "database_generator.py").write_text("")

    registry = GeneratorRegistry()

    generators = registry.discover(tmp_path)

    assert "cache_generator" in generators

    assert "database_generator" in generators

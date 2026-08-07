from oae.meta.generator_builder import GeneratorBuilder
from oae.meta.generator_spec import GeneratorSpecification


def test_generator_builder(tmp_path):

    spec = GeneratorSpecification(
        name="CacheGenerator",
        description="Redis Cache",
    )

    target = GeneratorBuilder().build(
        tmp_path,
        spec,
    )

    assert target.exists()

    assert "CacheGenerator" in target.read_text()

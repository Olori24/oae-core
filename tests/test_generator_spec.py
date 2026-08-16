from oae.meta.generator_spec import GeneratorSpecification


def test_generator_spec():

    spec = GeneratorSpecification(
        name="CacheGenerator",
        description="Redis cache support",
        directories=["src/cache"],
        files=["redis.py"],
    )

    assert spec.name == "CacheGenerator"

    assert spec.bootstrap is True

    assert spec.tests is True

    assert spec.documentation is True

    assert spec.directories == ["src/cache"]

    assert spec.files == ["redis.py"]

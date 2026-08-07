from oae.meta.generator_builder import GeneratorBuilder
from oae.meta.generator_spec import GeneratorSpecification
from oae.meta.generator_validator import GeneratorValidator


def test_generator_validator(tmp_path):

    spec = GeneratorSpecification(
        name="CacheGenerator",
        description="Redis Cache",
    )

    generator = GeneratorBuilder().build(
        tmp_path,
        spec,
    )

    assert (
        GeneratorValidator().validate(
            generator,
            spec,
        )
        is True
    )

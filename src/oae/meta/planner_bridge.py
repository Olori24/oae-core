from oae.meta.generator_spec import GeneratorSpecification


class PlannerBridge:
    """
    Converts missing engineering capabilities into
    generator specifications.
    """

    def create_specification(
        self,
        capability: str,
    ) -> GeneratorSpecification:

        name = (
            capability.replace(" ", "")
            + "Generator"
        )

        return GeneratorSpecification(
            name=name,
            description=f"Generates {capability}",
            directories=[],
            files=[],
        )

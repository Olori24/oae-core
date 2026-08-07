from pathlib import Path

from oae.meta.generator_spec import GeneratorSpecification


class GeneratorValidator:
    """
    Validates generators produced by the Meta Generator Engine.
    """

    def validate(
        self,
        generator_file: Path,
        spec: GeneratorSpecification,
    ) -> bool:

        generator_file = Path(generator_file)

        if not generator_file.exists():
            return False

        content = generator_file.read_text()

        required = [
            f"class {spec.name}",
            "def generate",
            '"""',
        ]

        for item in required:
            if item not in content:
                return False

        return True

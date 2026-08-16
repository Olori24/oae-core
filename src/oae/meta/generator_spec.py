from dataclasses import dataclass, field


@dataclass(slots=True)
class GeneratorSpecification:
    """
    Describes a generator that can be created by OAE.
    """

    name: str

    description: str

    directories: list[str] = field(default_factory=list)

    files: list[str] = field(default_factory=list)

    bootstrap: bool = True

    tests: bool = True

    documentation: bool = True

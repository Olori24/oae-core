from pathlib import Path


class GeneratorRegistry:
    """
    Discovers OAE generators.
    """

    def discover(self, root):

        root = Path(root)

        core = root / "src" / "oae" / "core"

        generators = []

        for file in core.glob("*_generator.py"):

            generators.append(file.stem)

        return sorted(generators)

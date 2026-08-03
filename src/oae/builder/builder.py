from oae.security.kernel import SecurityKernel

from .architect import Architect
from .generator import Generator


class Builder:
    """Builds new subsystems from engineering missions."""

    def __init__(self):
        self.architect = Architect()
        self.generator = Generator()
        self.security = SecurityKernel()

    def build(self, mission):

        if not self.security.authorize("write_repository"):
            print("Security denied repository write.")
            return False

        module = mission.lower().replace(" ", "_")

        files = self.architect.plan(module)

        result = self.generator.create(module, files)

        print(f"Mission completed: {result}")

        return True

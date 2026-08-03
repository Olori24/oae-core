from .architect import Architect
from .generator import Generator


class Builder:

    def __init__(self):
        self.architect = Architect()
        self.generator = Generator()

    def build(self, mission):

        module = mission.lower().replace(" ", "_")

        files = self.architect.plan(module)

        result = self.generator.create(module, files)

        print(f"Mission completed: {result}")

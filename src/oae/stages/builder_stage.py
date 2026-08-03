"""
Builder stage.
"""

from oae.core.stage import Stage
from oae.builder.builder import Builder


class BuilderStage(Stage):

    name = "Builder"

    def __init__(self):
        self.builder = Builder()

    def execute(self, context):
        """
        Execute the Builder stage.
        """

        result = self.builder.build(context.mission)

        context.metadata["builder_result"] = result
        context.metadata["builder_completed"] = True

        return context

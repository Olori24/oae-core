"""
Engineering Pipeline.

Coordinates engineering workflows through registered stages.
"""

from .context import EngineeringContext
from .stage_registry import StageRegistry


class EngineeringPipeline:
    """Coordinates autonomous engineering missions."""

    def __init__(self):
        self.stages = StageRegistry().load()

    def execute(self, mission):

        context = EngineeringContext(mission)

        print(f"Mission received: {mission}")

        for stage in self.stages:

            context.record(stage.name, "started")

            context = stage.execute(context)

            context.record(stage.name, "completed")

        print("Pipeline completed.")

        return context

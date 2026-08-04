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

    def execute(self, context):

        if not isinstance(context, EngineeringContext):
            context = EngineeringContext(context)

        print(f"Mission received: {context.mission}")

        for stage in self.stages:

            try:
                context = stage.run(context)

            except Exception as exc:

                context.success = False
                context.failed_stage = stage.name
                context.error = str(exc)

                context.record(stage.name, "failed")
                break

        context.complete()

        print("Pipeline completed.")

        return context

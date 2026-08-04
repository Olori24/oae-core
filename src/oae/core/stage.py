"""
Base Stage for the Engineering Pipeline.
"""


class Stage:
    """Base class for all pipeline stages."""

    name = "Stage"

    def before_execute(self, context):
        """Hook executed before the stage."""
        return context

    def execute(self, context):
        """Override in subclasses."""
        raise NotImplementedError

    def after_execute(self, context):
        """Hook executed after the stage."""
        return context

    def run(self, context):
        """Execute the complete stage lifecycle."""

        context.record(self.name, "started")

        context = self.before_execute(context)

        context = self.execute(context)

        context = self.after_execute(context)

        context.record(self.name, "completed")

        return context

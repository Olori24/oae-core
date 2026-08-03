"""
Base stage for the OAE Engineering Pipeline.
"""


class Stage:
    """Base class for all pipeline stages."""

    name = "Stage"

    def execute(self, context):
        """
        Execute the stage.

        Args:
            context: EngineeringContext

        Returns:
            Updated context.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement execute()."
        )

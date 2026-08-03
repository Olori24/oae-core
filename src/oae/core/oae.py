"""
Open Autonomous Engineer
"""

from .pipeline import EngineeringPipeline


class OAE:
    """Main public interface for OAE."""

    def __init__(self):
        self.pipeline = EngineeringPipeline()

    def execute(self, mission):
        """Execute an engineering mission."""
        return self.pipeline.execute(mission)

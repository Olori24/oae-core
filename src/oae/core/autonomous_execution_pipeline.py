from oae.core.unified_assignment_engine import UnifiedAssignmentEngine


class AutonomousExecutionPipeline:
    """
    End-to-end autonomous mission pipeline.
    """

    def __init__(self):
        self.assignment_engine = UnifiedAssignmentEngine()

    def register(self, agent):
        self.assignment_engine.register(agent)

    def execute(self, mission):
        return self.assignment_engine.assign(mission)
from oae.core.mission_lifecycle import MissionStatus


class WorkflowGovernor:
    """
    Validates legal mission status transitions.
    """

    _transitions = {
        MissionStatus.CREATED: [MissionStatus.PLANNING],
        MissionStatus.PLANNING: [MissionStatus.ARCHITECTURE],
        MissionStatus.ARCHITECTURE: [MissionStatus.IMPLEMENTATION],
        MissionStatus.IMPLEMENTATION: [MissionStatus.QA],
        MissionStatus.QA: [MissionStatus.SECURITY],
        MissionStatus.SECURITY: [MissionStatus.DEPLOYMENT],
        MissionStatus.DEPLOYMENT: [MissionStatus.COMPLETED],
        MissionStatus.COMPLETED: [],
    }

    def is_valid(
        self,
        current: MissionStatus,
        new: MissionStatus,
    ) -> bool:
        return new in self._transitions[current]
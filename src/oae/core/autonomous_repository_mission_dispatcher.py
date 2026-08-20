

class AutonomousRepositoryMissionDispatcher:
    """
    Dispatches engineering missions to managed repositories.
    """

    def __init__(self):
        self._missions = {}

    def dispatch(self, repository, mission):
        self._missions.setdefault(repository, [])
        self._missions[repository].append(mission)

    def missions(self, repository):
        return self._missions.get(repository, [])

    def repositories(self):
        return sorted(self._missions.keys())

    def clear(self, repository):
        self._missions[repository] = []

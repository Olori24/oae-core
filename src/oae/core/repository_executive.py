class RepositoryExecutive:
    """
    Determines which repository should receive engineering attention next.
    """

    def __init__(self):
        self._repositories = {}

    def register(self, repository_name):
        self._repositories.setdefault(repository_name, [])

    def add_mission(self, repository_name, mission):
        self.register(repository_name)
        self._repositories[repository_name].append(mission)

    def next_repository(self):
        if not self._repositories:
            return None

        ranked = sorted(
            self._repositories.items(),
            key=lambda item: len(item[1]),
            reverse=True,
        )

        return ranked[0][0]

    def mission_count(self, repository_name):
        return len(
            self._repositories.get(repository_name, [])
        )

    def repositories(self):
        return sorted(self._repositories.keys())

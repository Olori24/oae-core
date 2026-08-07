class CapabilityDependencyGraph:
    """
    Stores engineering capability dependencies.
    """

    def __init__(self):

        self._graph = {
            "Authorization": [
                "Authentication",
            ],
            "RBAC": [
                "Authorization",
            ],
            "Audit Logging": [
                "RBAC",
            ],
            "Docker Compose": [
                "Docker",
            ],
            "Container Deployment": [
                "Docker Compose",
            ],
            "Kubernetes": [
                "Container Deployment",
            ],
        }

    def dependencies_for(
        self,
        capability,
    ):
        return self._graph.get(
            capability,
            [],
        )

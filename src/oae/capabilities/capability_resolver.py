from oae.capabilities.capability_dependency_graph import (
    CapabilityDependencyGraph,
)


class CapabilityResolver:
    """
    Resolves all prerequisite capabilities.
    """

    def __init__(self):

        self.graph = CapabilityDependencyGraph()

    def resolve(self, capability):

        resolved = []

        self._resolve(capability, resolved)

        return resolved

    def _resolve(self, capability, resolved):

        for dependency in self.graph.dependencies_for(
            capability,
        ):
            self._resolve(
                dependency,
                resolved,
            )

        if capability not in resolved:
            resolved.append(capability)

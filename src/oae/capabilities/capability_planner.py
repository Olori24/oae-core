from dataclasses import dataclass

from oae.capabilities.capability import Capability


@dataclass(slots=True)
class CapabilityMission:
    """
    Engineering mission generated
    from discovered capabilities.
    """

    title: str
    priority: int
    description: str


class CapabilityPlanner:
    """
    Converts engineering findings into
    executable missions.
    """

    def plan(
        self,
        capabilities,
        semantic_findings=None,
    ):

        if semantic_findings is None:
            semantic_findings = []

        missions = []

        for capability in capabilities:

            missions.append(
                CapabilityMission(
                    title=f"Implement {capability.name}",
                    priority=capability.priority,
                    description=capability.description,
                )
            )

        for finding in semantic_findings:

            name, description, priority = finding

            missions.append(
                CapabilityMission(
                    title=f"Implement {name}",
                    priority=priority,
                    description=description,
                )
            )

        missions.sort(
            key=lambda mission: mission.priority
        )

        return missions

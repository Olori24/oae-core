from pathlib import Path

from oae.capabilities.capability_discovery_engine import (
    CapabilityDiscoveryEngine,
)
from oae.capabilities.capability_planner import (
    CapabilityPlanner,
)
from oae.capabilities.semantic_repository_analyzer import (
    SemanticRepositoryAnalyzer,
)


class EngineeringReviewEngine:

    def __init__(self):

        self.discovery = CapabilityDiscoveryEngine()

        self.semantic = SemanticRepositoryAnalyzer()

        self.planner = CapabilityPlanner()

    def review(self, root):

        root = Path(root)

        capabilities = self.discovery.discover(root)

        semantic = self.semantic.analyze(root)

        missions = self.planner.plan(
            capabilities,
            semantic,
        )

        return {
            "repository": root.name,
            "health_score": self._health_score(
                capabilities,
                semantic,
            ),
            "capabilities": capabilities,
            "semantic_findings": semantic,
            "missions": missions,
        }

    def _health_score(
        self,
        capabilities,
        semantic,
    ):

        deductions = (
            len(capabilities) * 5
            + len(semantic) * 3
        )

        return max(
            100 - deductions,
            0,
        )

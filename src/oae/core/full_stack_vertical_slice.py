from pathlib import Path

from oae.core.application_quality_gate import ApplicationQualityGate
from oae.core.project_bootstrap_orchestrator import ProjectBootstrapOrchestrator
from oae.core.project_specification import ProjectSpecification


class FullStackVerticalSlice:
    """Generate and verify one complete application slice through OAE."""

    def __init__(self, bootstrap=None, quality_gate=None):
        self.bootstrap = bootstrap or ProjectBootstrapOrchestrator()
        self.quality_gate = quality_gate or ApplicationQualityGate()

    def execute(self, root, specification: ProjectSpecification):
        root = Path(root)
        self.bootstrap.bootstrap(root, specification)
        gate = self.quality_gate.evaluate(root, specification)
        return {
            "status": gate["status"],
            "root": str(root),
            "application": specification.name,
            "readiness_score": gate["readiness_score"],
            "verified": gate["verified"],
            "blockers": gate["blockers"],
            "verification": gate["verification"],
        }

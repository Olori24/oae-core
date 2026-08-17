from pathlib import Path

from oae.core.application_quality_gate import ApplicationQualityGate
from oae.core.project_bootstrap_orchestrator import ProjectBootstrapOrchestrator
from oae.core.project_specification import ProjectSpecification
from oae.core.vertical_slice_contract import VerticalSliceContract


class FullStackVerticalSlice:
    """Generate, validate, and verify one complete application slice through OAE."""

    def __init__(self, bootstrap=None, quality_gate=None, contract=None):
        self.bootstrap = bootstrap or ProjectBootstrapOrchestrator()
        self.quality_gate = quality_gate or ApplicationQualityGate()
        self.contract = contract or VerticalSliceContract()

    def execute(self, root, specification: ProjectSpecification):
        root = Path(root)
        self.bootstrap.bootstrap(root, specification)
        contract = self.contract.validate(root)
        if not contract["passed"]:
            return {
                "status": "blocked",
                "root": str(root),
                "application": specification.name,
                "readiness_score": 0,
                "verified": False,
                "blockers": [name for name, passed in contract["checks"].items() if not passed],
                "contract": contract,
                "verification": None,
            }

        gate = self.quality_gate.evaluate(root, specification)
        return {
            "status": gate["status"],
            "root": str(root),
            "application": specification.name,
            "readiness_score": gate["readiness_score"],
            "verified": gate["verified"],
            "blockers": gate["blockers"],
            "contract": contract,
            "verification": gate["verification"],
        }

from oae.core.application_verification_engine import ApplicationVerificationEngine
from oae.core.project_specification import ProjectSpecification


class ApplicationQualityGate:
    """Single production-candidate gate for generated applications."""

    def __init__(self, verifier=None):
        self.verifier = verifier or ApplicationVerificationEngine()

    def evaluate(self, root, specification: ProjectSpecification):
        result = self.verifier.verify(
            root,
            specification,
            execute_frontend_build=True,
        )
        blockers = [
            check["detail"]
            for check in result["checks"]
            if not check.get("passed", False)
        ]

        return {
            "status": "production_candidate"
            if result["status"] == "verified"
            else "blocked",
            "verified": result["status"] == "verified",
            "readiness_score": result["readiness"]["score"],
            "blockers": blockers,
            "verification": result,
        }

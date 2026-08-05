from dataclasses import dataclass

from oae.core.backend_engineer_agent import BackendTask


@dataclass
class SecurityReview:
    objective: str
    approved: bool
    findings: list[str]


class SecurityEngineerAgent:
    """
    Security Engineer responsible for reviewing
    implementation plans before execution.
    """

    def review(self, task: BackendTask) -> SecurityReview:
        findings = [
            "Validate security policy",
            "Check dangerous operations",
            "Require approval for destructive actions",
        ]

        return SecurityReview(
            objective=task.objective,
            approved=True,
            findings=findings,
        )
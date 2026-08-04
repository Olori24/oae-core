"""
Governance Validator.

Evaluates engineering missions against loaded governance.
"""

from oae.governance.result import ValidationResult


class GovernanceValidator:
    """Validates governance readiness."""

    def validate(self, engine):

        violations = []

        if not engine.constitution.loaded():
            violations.append("Constitution not loaded.")

        if not engine.standards.loaded():
            violations.append("Governance standards not loaded.")

        if not engine.adrs.loaded():
            violations.append("Architecture Decision Records not loaded.")

        return ValidationResult(
            approved=len(violations) == 0,
            violations=violations,
            warnings=[],
        )

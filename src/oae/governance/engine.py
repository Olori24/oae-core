"""
Governance Engine.
"""

from oae.core.subsystem import Subsystem
from oae.governance.adr import ADRRepository
from oae.governance.constitution import Constitution
from oae.governance.standards import Standards
from oae.governance.validator import GovernanceValidator


class GovernanceEngine(Subsystem):
    """Coordinates governance resources."""

    name = "governance"
    dependencies = []

    def __init__(self):
        super().__init__()

        self.constitution = Constitution()
        self.standards = Standards()
        self.adrs = ADRRepository()
        self.validator = GovernanceValidator()

    def initialize(self):
        self.constitution.load()
        self.standards.load()
        self.adrs.load()

        result = self.validate()

        self._initialized = result.approved

        return result

    def validate(self):
        return self.validator.validate(self)
